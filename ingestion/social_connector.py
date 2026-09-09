"""
National Weather Big Data Analytics Platform (NWBDAP)
Social Media Ingestion Connector & Real-Time Stream Generator
Ingests and simulates high-velocity social feeds (#IMD, #MumbaiRains, #DelhiWeather, etc.)
"""

import random
import threading
import time
import uuid
from datetime import datetime, timezone
import config
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

    def emit_single_report(self):
        """Picks a template and injects a single realistic report into the queue."""
        template = random.choice(SAMPLE_STREAM_POOL)
        city_name = template["city"]
        city_meta = config.MAJOR_INDIAN_CITIES.get(city_name, {
            "lat": 28.6139, "lon": 77.2090, "state": template["state"]
        })

        # Add small spatial perturbation (within ~3-5km)
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
        """Periodic loop pushing simulated posts."""
        while self.is_streaming:
            try:
                self.emit_single_report()
            except Exception as e:
                print(f"[SOCIAL INGESTION ERROR] {e}")
            time.sleep(self.interval)

social_connector = SocialMediaConnector()
