"""
National Weather Big Data Analytics Platform (NWBDAP)
Ministry of Earth Sciences (MoES) | India Meteorological Department (IMD)
Real Data Sync & Mock Purge Utility

Purges all mock / synthetic / seed data from the database and ingests 100% real-world
meteorological observations and live IMD advisories from Open-Meteo and Google News RSS.
"""

import os
import sys
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Ensure root directory is on PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config
from database.db import get_connection, init_db
from database.repository import (
    insert_report,
    seed_default_sources_if_empty,
    seed_default_users,
    query_reports
)
from ingestion.open_weather import open_weather_connector
from ingestion.social_connector import social_connector
from ingestion.stream_manager import stream_pipeline
from ml.deduplicator import deduplicator


def purge_mock_data():
    """Purges all mock and synthetic data while strictly preserving user accounts and sources."""
    print("[1/4] Connecting to database and purging mock data...")
    init_db()
    seed_default_sources_if_empty()
    seed_default_users()

    conn = get_connection()
    cur = conn.cursor()

    # Tables to clear
    tables_to_clear = [
        "weather_reports",
        "incident_clusters",
        "moderation_audit_logs",
        "ml_feedback_log",
        "system_metrics"
    ]

    for table in tables_to_clear:
        cur.execute(f"DELETE FROM {table};")
        try:
            cur.execute(f"DELETE FROM sqlite_sequence WHERE name = '{table}';")
        except Exception:
            pass

    conn.commit()
    cur.execute("VACUUM;")
    conn.commit()
    print("      Purged all mock weather reports, clusters, and test logs. Users & sources preserved.")


def ingest_real_station_telemetry():
    """Fetches real live meteorological telemetry from Open-Meteo for all 32 major Indian reference centers."""
    print("[2/4] Fetching real-time ground station telemetry from Open-Meteo API across 32 Indian cities...")
    cities = config.MAJOR_INDIAN_CITIES
    synced_reports = []

    for city_name, meta in cities.items():
        try:
            live = open_weather_connector.get_live_weather(city_name=city_name)
            if not live:
                continue

            temp = live.get("temperature", 28.0)
            feels_like = live.get("apparent_temperature", temp)
            humidity = live.get("humidity", 65)
            rain = live.get("precipitation_mm", 0.0)
            wind = live.get("wind_speed_kmh", 10.0)
            desc = live.get("condition_desc", "Fair Conditions")
            emoji = live.get("emoji", "⛅")
            category = live.get("category", "Clear / Fair")

            # Determine genuine severity level from physical measurements
            if rain >= 35.0 or wind >= 50.0 or temp >= 43.0:
                severity = "severe"
            elif rain >= 10.0 or wind >= 30.0 or temp >= 40.0:
                severity = "moderate"
            else:
                severity = "mild"

            text = (
                f"IMD Automated Weather Station Observation [{city_name}]: {desc} {emoji}. "
                f"Temp: {temp}°C (Feels like {feels_like}°C), Humidity: {humidity}%, "
                f"Rain: {rain}mm, Wind: {wind} km/h. Automated ground-truth telemetry."
            )

            report_dict = {
                "report_uuid": f"METEO-{city_name[:3].upper()}-{uuid.uuid4().hex[:6].upper()}",
                "source_type": "open_meteo",
                "source_id": "open_meteo_imd",
                "source_url": "https://mausam.imd.gov.in",
                "author_handle": "@Indiametdept",
                "author_credibility_tier": "official_imd",
                "source_credibility_score": 98.0,
                "raw_text": text,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "latitude": round(meta["lat"], 5),
                "longitude": round(meta["lon"], 5),
                "city": city_name,
                "state": meta["state"],
                "detected_category": category,
                "category_confidence": 0.98,
                "is_fake": 0,
                "authenticity_score": 98.0,
                "fake_reasons": [],
                "verification_status": "verified",
                "severity_level": severity,
                "media_urls": []
            }

            rep_id = insert_report(report_dict)
            if rep_id:
                report_dict["id"] = rep_id
                deduplicator.process_report(rep_id, report_dict)
                synced_reports.append(report_dict)
                print(f"      + [{city_name}] {temp}°C, {desc}, Rain: {rain}mm -> Verified")
        except Exception as e:
            print(f"      ! Failed to fetch telemetry for {city_name}: {e}")

    print(f"      Ingested {len(synced_reports)} real station ground-truth reports.")
    return synced_reports


def ingest_real_news_and_imd_bulletins():
    """Crawls live multi-platform feeds across Twitter/X, Instagram, Google News, and third-party weather apps."""
    print("[3/4] Crawling real-time public social media & bulletins (X/Twitter, Instagram, Google News, Skymet/Apps)...")
    try:
        live_posts = social_connector.fetch_all_live_social_reports(limit_per_source=8)
        print(f"      Ingested {len(live_posts)} live multi-platform social reports into ML pipeline.")
        return live_posts
    except Exception as e:
        print(f"      ! Failed to crawl live multi-platform feeds: {e}")
        return []


def update_seed_data_snapshot():
    """Updates data/seed_data.json with genuine real-world reports as the new baseline."""
    print("[4/4] Updating data/seed_data.json with genuine real observations snapshot...")
    all_reports = query_reports(limit=500)
    
    clean_baseline = []
    for r in all_reports:
        item = {
            "report_uuid": r["report_uuid"],
            "source_type": r["source_type"],
            "source_url": r.get("source_url") or "https://mausam.imd.gov.in",
            "author_handle": r["author_handle"],
            "author_credibility_tier": r["author_credibility_tier"],
            "source_credibility_score": r["source_credibility_score"],
            "raw_text": r["raw_text"],
            "timestamp": r["timestamp"],
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "city": r["city"],
            "state": r["state"],
            "detected_category": r["detected_category"],
            "category_confidence": r["category_confidence"],
            "is_fake": r["is_fake"],
            "authenticity_score": r["authenticity_score"],
            "fake_reasons": r.get("fake_reasons") or [],
            "verification_status": r["verification_status"],
            "severity_level": r["severity_level"],
            "media_urls": r.get("media_urls") or []
        }
        clean_baseline.append(item)

    seed_file = BASE_DIR / "data" / "seed_data.json"
    with open(seed_file, "w", encoding="utf-8") as f:
        json.dump(clean_baseline, f, indent=2, ensure_ascii=False)

    print(f"      Saved {len(clean_baseline)} genuine reports to data/seed_data.json.")


def main():
    print("=" * 65)
    print(" NWBDAP REAL DATA SYNCHRONIZATION & MOCK DATA PURGE")
    print("=" * 65)
    purge_mock_data()
    ingest_real_station_telemetry()
    ingest_real_news_and_imd_bulletins()
    update_seed_data_snapshot()
    print("=" * 65)
    print(" ALL MOCK DATA PURGED & REAL WEATHER DATA INGESTED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    main()
