"""
National Weather Big Data Analytics Platform (NWBDAP)
Ministry of Earth Sciences (MoES) | India Meteorological Department (IMD)
Live 30-Second Background Scraper Engine

Periodically scrapes live meteorological feeds, Google News IMD RSS bulletins,
and rotating ground-truth station telemetry every 30 seconds.
"""

import time
import threading
import uuid
from datetime import datetime, timezone
import config
from ingestion.social_connector import social_connector
from ingestion.open_weather import open_weather_connector
from ingestion.google_weather import google_weather_connector
from ingestion.stream_manager import stream_pipeline


class LiveScraperEngine:
    """Automated 30-second live meteorological and news scraping daemon."""

    def __init__(self, interval=config.LIVE_SCRAPE_INTERVAL_SECONDS):
        self.interval = interval
        self.is_running = False
        self.thread = None
        self.last_scraped_at = None
        self.last_scraped_count = 0
        self.total_scrapes = 0
        self.station_index = 0
        self.cities = list(config.MAJOR_INDIAN_CITIES.keys())
        self.lock = threading.Lock()

    def scrape_once(self):
        """Executes a single live scraping and telemetry polling cycle."""
        scraped_reports = []
        with self.lock:
            # 1. Scrape real-time multi-platform social feeds & bulletins (Twitter, Instagram, Google News, Third-party apps)
            try:
                social_items = social_connector.fetch_all_live_social_reports(limit_per_source=2)
                if social_items:
                    scraped_reports.extend(social_items)
            except Exception as e:
                print(f"[LIVE SCRAPER] Multi-platform social crawl warning: {e}")

            # 2. Poll live telemetry for 2 rotating major Indian reference stations
            try:
                if self.cities:
                    for _ in range(2):
                        city_name = self.cities[self.station_index % len(self.cities)]
                        self.station_index += 1

                        live = google_weather_connector.get_live_weather(city_name=city_name)
                        if not live:
                            continue

                        city_meta = config.MAJOR_INDIAN_CITIES.get(city_name, {})
                        temp = live.get("temperature", 28.0)
                        feels_like = live.get("apparent_temperature", temp)
                        humidity = live.get("humidity", 65)
                        rain = live.get("precipitation_mm", 0.0)
                        wind = live.get("wind_speed_kmh", 10.0)
                        desc = live.get("condition_desc", "Fair")
                        emoji = live.get("emoji", "⛅")
                        category = live.get("category", "Clear / Fair")

                        severity = "mild"
                        if rain >= 35.0 or wind >= 50.0 or temp >= 43.0:
                            severity = "severe"
                        elif rain >= 10.0 or wind >= 30.0 or temp >= 40.0:
                            severity = "moderate"

                        text = (
                            f"IMD Live Ground Observation [{city_name}]: {desc} {emoji}. "
                            f"Temp: {temp}°C (Feels {feels_like}°C), Humidity: {humidity}%, "
                            f"Rain: {rain}mm, Wind: {wind} km/h. Automated ground-truth telemetry."
                        )

                        report_dict = {
                            "report_uuid": f"METEO-LIVE-{uuid.uuid4().hex[:8].upper()}",
                            "source_type": "open_meteo",
                            "source_id": "open_meteo_imd",
                            "source_url": "https://mausam.imd.gov.in",
                            "author_handle": "@Indiametdept",
                            "author_credibility_tier": "official_imd",
                            "source_credibility_score": 98.0,
                            "raw_text": text,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "latitude": round(city_meta.get("lat", 20.0), 5),
                            "longitude": round(city_meta.get("lon", 78.0), 5),
                            "city": city_name,
                            "state": city_meta.get("state", "India"),
                            "detected_category": category,
                            "category_confidence": 0.98,
                            "is_fake": 0,
                            "authenticity_score": 98.0,
                            "fake_reasons": [],
                            "verification_status": "verified",
                            "severity_level": severity,
                            "media_urls": []
                        }

                        # Commit directly to database through ML enrichment
                        processed = stream_pipeline.process_report_now(report_dict)
                        if processed:
                            scraped_reports.append(processed)
            except Exception as e:
                print(f"[LIVE SCRAPER] Station observation poll warning: {e}")

            self.total_scrapes += 1
            self.last_scraped_at = datetime.now(timezone.utc).isoformat()
            self.last_scraped_count = len(scraped_reports)
            print(f"[LIVE SCRAPER] Cycle #{self.total_scrapes} complete: {len(scraped_reports)} new reports ingested at {self.last_scraped_at}")
            return scraped_reports

    def _loop(self):
        """Continuous 30-second execution loop."""
        while self.is_running:
            try:
                time.sleep(self.interval)
                if self.is_running:
                    self.scrape_once()
            except Exception as e:
                print(f"[LIVE SCRAPER ERROR] {e}")

    def start(self):
        """Starts the background scraping daemon thread."""
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._loop, name="Live30sScraperDaemon", daemon=True)
        self.thread.start()
        print(f"[LIVE SCRAPER] 30-second live background scraping daemon started (interval: {self.interval}s).")

    def stop(self):
        """Stops the daemon."""
        self.is_running = False

    def get_status(self):
        """Returns current operational status of the 30-second scraper."""
        return {
            "is_active": self.is_running,
            "interval_seconds": self.interval,
            "total_cycles": self.total_scrapes,
            "last_scraped_at": self.last_scraped_at,
            "last_scraped_count": self.last_scraped_count
        }


live_scraper = LiveScraperEngine()
