"""
National Weather Big Data Analytics Platform (NWBDAP)
Social Media Ingestion Connector & Real-Time Stream Generator
Ingests and simulates high-velocity social feeds (#IMD, #MumbaiRains, #DelhiWeather, etc.)
"""

import random
import threading
import time
import uuid
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import requests
import config
from data.india_districts import extract_location_from_text
from ingestion.stream_manager import stream_pipeline

# Rich pool of realistic weather posts reflecting actual Indian meteorology and social platforms
SAMPLE_STREAM_POOL = [
    # Genuine Reports
    {
        "author_handle": "@mumbairains_updates",
        "platform": "twitter",
        "source_id": "tw_mumbai_rains",
        "city": "Mumbai",
        "state": "Maharashtra",
        "text": "Waterlogging reported near Sion circle and Hindmata Dadar. BMC pumps active. Avoid Dr Ambedkar road. #MumbaiRains #IMD",
        "severity": "severe",
        "lat_offset": 0.01, "lon_offset": -0.01,
        "media": ["https://images.unsplash.com/photo-1515694346937-94d85e41e6f0?w=600"]
    },
    {
        "author_handle": "@Indiametdept",
        "platform": "twitter",
        "source_id": "tw_imd_official",
        "city": "New Delhi",
        "state": "Delhi",
        "text": "Press Release: Moderate to intense thunderstorm accompanied with gusty winds (speed 40-50 kmph) likely over Delhi-NCR during next 3 hours. #IMD #DelhiWeather",
        "severity": "moderate",
        "lat_offset": 0.0, "lon_offset": 0.0,
        "media": []
    },
    {
        "author_handle": "@bangalore_citizen",
        "platform": "twitter",
        "source_id": "tw_imd_official",
        "city": "Bengaluru",
        "state": "Karnataka",
        "text": "Sudden torrential cloudburst in Bellandur and Marathahalli! Underpasses filled with water, huge traffic jam on ORR. #BengaluruRains #IMD",
        "severity": "severe",
        "lat_offset": -0.02, "lon_offset": 0.03,
        "media": ["https://images.unsplash.com/photo-1547683905-f686c993aae5?w=600"]
    },
    {
        "author_handle": "@chennai_weatherman",
        "platform": "twitter",
        "source_id": "tw_imd_official",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "text": "Heavy convective showers sweeping across Velachery, Guindy and OMR corridor. Rain rate around 35mm/hr currently. #ChennaiRains #TamilNaduWeather",
        "severity": "moderate",
        "lat_offset": -0.01, "lon_offset": 0.01,
        "media": []
    },
    {
        "author_handle": "@rajasthan_pulse",
        "platform": "twitter",
        "source_id": "tw_imd_official",
        "city": "Jaipur",
        "state": "Rajasthan",
        "text": "Intense heatwave continues unabated! Mercury touched 46.5°C in Jaipur and 48°C in Barmer today. Avoid outdoor activities in afternoon! #HeatwaveIndia #Loo",
        "severity": "extreme",
        "lat_offset": 0.0, "lon_offset": 0.0,
        "media": []
    },
    {
        "author_handle": "@kolkata_diaries",
        "platform": "instagram",
        "source_id": "ig_weather_photos",
        "city": "Kolkata",
        "state": "West Bengal",
        "text": "Severe Kalbaishakhi nor'wester storm hit Kolkata! Tree branches fallen in Park Street, heavy thunder flashes illuminating the Hooghly. #KolkataWeather #Thunderstorm",
        "severity": "severe",
        "lat_offset": 0.02, "lon_offset": -0.01,
        "media": ["https://images.unsplash.com/photo-1605721911519-3dfeb3be25e7?w=600"]
    },
    {
        "author_handle": "@himachal_live",
        "platform": "twitter",
        "source_id": "tw_imd_official",
        "city": "Shimla",
        "state": "Himachal Pradesh",
        "text": "Heavy hailstorm reported along with fresh snowfall at higher reaches of Kufri and Narkanda. Roads slippery, drive with caution. #ShimlaSnow #Hailstorm",
        "severity": "moderate",
        "lat_offset": 0.01, "lon_offset": 0.02,
        "media": ["https://images.unsplash.com/photo-1491555103944-7c647fd857e6?w=600"]
    },
    {
        "author_handle": "@odisha_disaster_alert",
        "platform": "twitter",
        "source_id": "tw_cyclone_watch",
        "city": "Bhubaneswar",
        "state": "Odisha",
        "text": "Cyclone warning: Deep depression over west-central Bay of Bengal heading towards coastal Odisha. Sea condition rough, squally wind speeds reaching 65 kmph. #CycloneAlert",
        "severity": "extreme",
        "lat_offset": 0.0, "lon_offset": 0.0,
        "media": []
    },
    {
        "author_handle": "@delhi_commuter",
        "platform": "twitter",
        "source_id": "tw_imd_official",
        "city": "New Delhi",
        "state": "Delhi",
        "text": "Dense smog and zero visibility at DND Flyway this morning. Eyes stinging, AQI meter reading above 420. Drive with hazard lights on. #DelhiAirPollution #Smog",
        "severity": "severe",
        "lat_offset": 0.01, "lon_offset": 0.01,
        "media": []
    },
    {
        "author_handle": "@bikaner_express",
        "platform": "twitter",
        "source_id": "tw_imd_official",
        "city": "Jaipur",
        "state": "Rajasthan",
        "text": "Fierce dust storm and aandhi hitting northern ring road! Sand blowing across the highway, zero visibility at 50 meters. #DustStorm #RajasthanWeather",
        "severity": "moderate",
        "lat_offset": 0.03, "lon_offset": -0.02,
        "media": []
    },

    # Misleading / Fake Posts (To Demonstrate AI Filtering & Fake Detector)
    {
        "author_handle": "@viral_buzz_994827",
        "platform": "twitter",
        "source_id": "tw_mumbai_rains",
        "city": "Mumbai",
        "state": "Maharashtra",
        "text": "UNBELIEVABLE APOCALYPSE IN MUMBAI!!!! ENTIRE CITY SUBMERGED UNDERWATER RUN FOR YOUR LIVES!!!! DOOMSDAY DELUGE OF THE CENTURY!!!! #MumbaiDrowning",
        "severity": "extreme",
        "lat_offset": 0.0, "lon_offset": 0.0,
        "media": []
    },
    {
        "author_handle": "@hoax_bot_19283",
        "platform": "twitter",
        "source_id": "tw_imd_official",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "text": "SHOCKING: Heavy snowfall in Chennai Marina Beach today morning! Freezing baraf falling everywhere tourists stunned! #ChennaiSnow #Miracle",
        "severity": "extreme",
        "lat_offset": 0.0, "lon_offset": 0.0,
        "media": []
    },
    {
        "author_handle": "@weather_conspiracy_x",
        "platform": "twitter",
        "source_id": "tw_imd_official",
        "city": "New Delhi",
        "state": "Delhi",
        "text": "Severe tropical cyclone landfall happening directly over Connaught Place Delhi tonight!! Secret government weather weapon HAARP created this hurricane!!",
        "severity": "extreme",
        "lat_offset": 0.0, "lon_offset": 0.0,
        "media": []
    }
]

class SocialMediaConnector:
    """Simulates real-time social media ingestion stream."""

    def __init__(self):
        self.is_streaming = False
        self.stream_thread = None
        self.interval = config.SIMULATION_STREAM_INTERVAL_SECONDS
        self.seen_post_hashes = set()
        self._cached_live_posts = []

    def start_stream(self, interval=None):
        """Starts real-time simulated stream thread."""
        if self.is_streaming:
            return

        if interval:
            self.interval = interval

        self.is_streaming = True
        self.stream_thread = threading.Thread(target=self._stream_loop, name="SocialStreamGen", daemon=True)
        self.stream_thread.start()
        print(f"[SOCIAL INGESTION] Live social media stream activated (interval: {self.interval}s).")

    def stop_stream(self):
        """Stops the live stream generator."""
        self.is_streaming = False
        print("[SOCIAL INGESTION] Live social media stream paused.")

    def fetch_live_imd_social_posts(self, limit=15):
        """
        Crawls and ingests up-to-the-minute real-world weather reports and #IMD updates
        from live public Google News / IMD weather RSS syndication and Mastodon #IMD timelines.
        """
        new_reports = []
        feed_url = "https://news.google.com/rss/search?q=IMD+weather+OR+alert+OR+rainfall+India&hl=en-IN&gl=IN&ceid=IN:en"

        try:
            resp = requests.get(feed_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=6.0)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                items = root.findall(".//item")
                for item in items[:limit]:
                    title = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else "https://mausam.imd.gov.in"
                    source_elem = item.find("source")
                    source_name = source_elem.text if source_elem is not None else "IMD Media"

                    if not title:
                        continue

                    post_id = str(hash(title))
                    if post_id in self.seen_post_hashes:
                        continue
                    self.seen_post_hashes.add(post_id)

                    clean_source = re.sub(r'[^a-zA-Z0-9_]', '', source_name).lower()
                    author_handle = f"@{clean_source[:18]}_imd" if clean_source else "@indiametdept"

                    raw_text = title
                    if "#IMD" not in raw_text.upper():
                        raw_text += " #IMD #WeatherAlert"

                    state, district, lat, lon = extract_location_from_text(raw_text)

                    text_lower = raw_text.lower()
                    if any(w in text_lower for w in ["extremely heavy", "cloudburst", "red alert", "cyclone", "flash flood", "warning"]):
                        severity = "severe"
                    elif any(w in text_lower for w in ["heavy rain", "thunderstorm", "alert", "gusty", "hail"]):
                        severity = "moderate"
                    else:
                        severity = "mild"

                    iso_ts = datetime.now(timezone.utc).isoformat()
                    report_dict = {
                        "report_uuid": f"SOC-LIVE-{uuid.uuid4().hex[:10].upper()}",
                        "source_type": "twitter",
                        "source_id": "social_live_imd",
                        "source_url": link,
                        "author_handle": author_handle,
                        "raw_text": raw_text,
                        "timestamp": iso_ts,
                        "latitude": round(lat, 5),
                        "longitude": round(lon, 5),
                        "city": district,
                        "state": state,
                        "severity_level": severity,
                        "media_urls": []
                    }

                    processed = stream_pipeline.process_report_now(report_dict)
                    new_reports.append(processed)

        except Exception as e:
            print(f"[LIVE SOCIAL CRAWLER] RSS fetch error: {e}")

        # Also query Mastodon for #IMD hashtag posts
        try:
            m_resp = requests.get("https://mastodon.social/api/v1/timelines/tag/IMD", timeout=4.0)
            if m_resp.status_code == 200:
                m_posts = m_resp.json()
                for p in m_posts[:5]:
                    content_html = p.get("content", "")
                    clean_content = re.sub(r'<[^>]+>', '', content_html).strip()
                    if not clean_content:
                        continue
                    post_id = str(p.get("id"))
                    if post_id in self.seen_post_hashes:
                        continue
                    self.seen_post_hashes.add(post_id)

                    account = p.get("account", {})
                    author_handle = f"@{account.get('username', 'citizen_reporter')}"
                    state, district, lat, lon = extract_location_from_text(clean_content)

                    report_dict = {
                        "report_uuid": f"SOC-MASTO-{uuid.uuid4().hex[:10].upper()}",
                        "source_type": "mastodon",
                        "source_id": "social_live_imd",
                        "source_url": p.get("url", "https://mastodon.social"),
                        "author_handle": author_handle,
                        "raw_text": clean_content if "#IMD" in clean_content.upper() else clean_content + " #IMD",
                        "timestamp": p.get("created_at", datetime.now(timezone.utc).isoformat()),
                        "latitude": round(lat, 5),
                        "longitude": round(lon, 5),
                        "city": district,
                        "state": state,
                        "severity_level": "moderate",
                        "media_urls": []
                    }
                    processed = stream_pipeline.process_report_now(report_dict)
                    new_reports.append(processed)
        except Exception as e:
            print(f"[LIVE SOCIAL CRAWLER] Mastodon error: {e}")

        if new_reports:
            self._cached_live_posts.extend(new_reports)

        print(f"[LIVE SOCIAL CRAWLER] Successfully ingested {len(new_reports)} live #IMD social reports.")
        return new_reports

    def ingest_custom_social_post(self, raw_text, author_handle=None, source_url=None, platform="twitter", media_urls=None):
        """
        Ingests and immediately analyzes an arbitrary user-supplied live tweet or social media post.
        """
        raw_text = (raw_text or "").strip()
        if not raw_text:
            raise ValueError("Social media post text cannot be empty.")

        if not author_handle or not author_handle.strip():
            author_handle = "@imd_crowd_intel"
        elif not author_handle.startswith("@"):
            author_handle = f"@{author_handle}"

        if "#IMD" not in raw_text.upper():
            raw_text += " #IMD"

        state, district, lat, lon = extract_location_from_text(raw_text)

        text_lower = raw_text.lower()
        if any(w in text_lower for w in ["extremely heavy", "cloudburst", "red alert", "cyclone", "flash flood", "warning"]):
            severity = "severe"
        elif any(w in text_lower for w in ["heavy rain", "thunderstorm", "alert", "gusty", "hail"]):
            severity = "moderate"
        else:
            severity = "mild"

        report_dict = {
            "report_uuid": f"SOC-USER-{uuid.uuid4().hex[:10].upper()}",
            "source_type": platform or "twitter",
            "source_id": "social_user_intake",
            "source_url": source_url or f"https://x.com/{author_handle.lstrip('@')}/status/live",
            "author_handle": author_handle,
            "raw_text": raw_text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": round(lat, 5),
            "longitude": round(lon, 5),
            "city": district,
            "state": state,
            "severity_level": severity,
            "media_urls": media_urls or []
        }

        # Enrich synchronously and return report with full ML predictions
        return stream_pipeline.process_report_now(report_dict)

    def emit_single_report(self):
        """Picks a live post or curated scenario report and enqueues it."""
        # Check if we have unconsumed live posts in memory buffer
        if self._cached_live_posts:
            return self._cached_live_posts.pop(0)

        template = random.choice(SAMPLE_STREAM_POOL)
        city_name = template["city"]
        city_meta = config.MAJOR_INDIAN_CITIES.get(city_name, {
            "lat": 28.6139, "lon": 77.2090, "state": template["state"]
        })

        lat = city_meta["lat"] + template.get("lat_offset", 0.0) + (random.uniform(-0.02, 0.02))
        lon = city_meta["lon"] + template.get("lon_offset", 0.0) + (random.uniform(-0.02, 0.02))

        report_dict = {
            "report_uuid": f"SOC-{uuid.uuid4().hex[:10].upper()}",
            "source_type": template["platform"],
            "source_id": template["source_id"],
            "source_url": f"https://x.com/{template['author_handle'].lstrip('@')}/status/{random.randint(1800000000000000, 1899999999999999)}",
            "author_handle": template["author_handle"],
            "raw_text": template["text"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": round(lat, 5),
            "longitude": round(lon, 5),
            "city": city_name,
            "state": template["state"],
            "severity_level": template["severity"],
            "media_urls": template.get("media", [])
        }

        stream_pipeline.push_raw_report(report_dict)
        return report_dict

    def _stream_loop(self):
        """Periodic loop pushing live and simulated posts."""
        cycle = 0
        while self.is_streaming:
            try:
                cycle += 1
                # Periodically crawl real live #IMD posts every 5 cycles
                if cycle % 5 == 0:
                    self.fetch_live_imd_social_posts(limit=5)
                self.emit_single_report()
            except Exception as e:
                print(f"[SOCIAL INGESTION ERROR] {e}")
            time.sleep(self.interval)

social_connector = SocialMediaConnector()
