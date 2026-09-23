"""
National Weather Big Data Analytics Platform (NWBDAP)
Ministry of Earth Sciences (MoES) | India Meteorological Department (IMD)
Problem Statement ID: 26069
System Configuration
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Database & Supabase Configuration
DB_PATH = BASE_DIR / "weather_platform.db"
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()
USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY and SUPABASE_URL.startswith("http"))

# Server Configuration
PORT = int(os.environ.get("PORT", 5005))
HOST = os.environ.get("HOST", "0.0.0.0")
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")
SECRET_KEY = os.environ.get("SECRET_KEY", "imd-moes-national-weather-analytics-2026-secret")

# Google Maps Platform / Google Weather API Configuration
GOOGLE_MAPS_API_KEY = (
    os.environ.get("GOOGLE_MAPS_API_KEY") or
    os.environ.get("GOOGLE_WEATHER_API_KEY") or
    os.environ.get("GOOGLE_API_KEY") or
    ""
).strip()
WEATHER_PROVIDER = os.environ.get("WEATHER_PROVIDER", "free" if not GOOGLE_MAPS_API_KEY else "auto").strip().lower()
GMP_SOLUTION_ID = "gmp_git_agentskills_v1"

# Ingestion & Streaming Configuration
QUEUE_MAXSIZE = 10000
INGESTION_WORKERS = 4
SIMULATION_STREAM_INTERVAL_SECONDS = 4  # New synthetic/real-time post every 4 seconds in live mode
LIVE_SCRAPE_INTERVAL_SECONDS = 30       # Background scraper & frontend auto-refresh cycle (30 seconds)

# AI / ML Thresholds
FAKE_SCORE_THRESHOLD = 50.0  # Scores < 50% deemed fake/misleading
DEDUP_RADIUS_KM = 15.0       # Spatial radius for duplicate clustering
DEDUP_TIME_HOURS = 2.0       # Temporal window for duplicate clustering
DEDUP_TEXT_SIMILARITY = 0.35 # Jaccard/TF-IDF threshold for duplicate candidate

# Weather Event Categories (IMD Standard Categories)
WEATHER_CATEGORIES = [
    "Clear / Fair",
    "Rainfall",
    "Thunderstorm",
    "Flooding",
    "Heatwave",
    "Fog/Smog",
    "Dust Storm",
    "Strong Winds",
    "Hailstorm",
    "Cyclone",
    "Snowfall"
]

# Source Credibility Default Weights
SOURCE_CREDIBILITY_MAP = {
    "official_imd": 98.0,
    "disaster_mgmt": 95.0,
    "verified_media": 88.0,
    "citizen_verified": 80.0,
    "social_public": 60.0,
    "anonymous": 40.0,
    "bot_flagged": 10.0
}

# Major Indian Meteorological Reference Centers & Coordinates
MAJOR_INDIAN_CITIES = {
    "New Delhi": {"lat": 28.6139, "lon": 77.2090, "state": "Delhi", "zone": "North"},
    "Mumbai": {"lat": 19.0760, "lon": 72.8777, "state": "Maharashtra", "zone": "West"},
    "Bengaluru": {"lat": 12.9716, "lon": 77.5946, "state": "Karnataka", "zone": "South"},
    "Chennai": {"lat": 13.0827, "lon": 80.2707, "state": "Tamil Nadu", "zone": "South"},
    "Kolkata": {"lat": 22.5726, "lon": 88.3639, "state": "West Bengal", "zone": "East"},
    "Hyderabad": {"lat": 17.3850, "lon": 78.4867, "state": "Telangana", "zone": "South"},
    "Ahmedabad": {"lat": 23.0225, "lon": 72.5714, "state": "Gujarat", "zone": "West"},
    "Jaipur": {"lat": 26.9124, "lon": 75.7873, "state": "Rajasthan", "zone": "North"},
    "Lucknow": {"lat": 26.8467, "lon": 80.9462, "state": "Uttar Pradesh", "zone": "North"},
    "Patna": {"lat": 25.5941, "lon": 85.1376, "state": "Bihar", "zone": "East"},
    "Bhubaneswar": {"lat": 20.2961, "lon": 85.8245, "state": "Odisha", "zone": "East"},
    "Guwahati": {"lat": 26.1445, "lon": 91.7362, "state": "Assam", "zone": "Northeast"},
    "Srinagar": {"lat": 34.0837, "lon": 74.7973, "state": "Jammu and Kashmir", "zone": "North"},
    "Shimla": {"lat": 31.1048, "lon": 77.1734, "state": "Himachal Pradesh", "zone": "North"},
    "Dehradun": {"lat": 30.3165, "lon": 78.0322, "state": "Uttarakhand", "zone": "North"},
    "Kochi": {"lat": 9.9312, "lon": 76.2673, "state": "Kerala", "zone": "South"},
    "Bhopal": {"lat": 23.2599, "lon": 77.4126, "state": "Madhya Pradesh", "zone": "Central"},
    "Ranchi": {"lat": 23.3441, "lon": 85.3096, "state": "Jharkhand", "zone": "East"},
    "Chandigarh": {"lat": 30.7333, "lon": 76.7794, "state": "Punjab", "zone": "North"},
    "Visakhapatnam": {"lat": 17.6868, "lon": 83.2185, "state": "Andhra Pradesh", "zone": "South"},
    "Pune": {"lat": 18.5204, "lon": 73.8567, "state": "Maharashtra", "zone": "West"},
    "Nagpur": {"lat": 21.1458, "lon": 79.0882, "state": "Maharashtra", "zone": "Central"},
    "Surat": {"lat": 21.1702, "lon": 72.8311, "state": "Gujarat", "zone": "West"},
    "Indore": {"lat": 22.7196, "lon": 75.8577, "state": "Madhya Pradesh", "zone": "Central"},
    "Amritsar": {"lat": 31.6340, "lon": 74.8723, "state": "Punjab", "zone": "North"},
    "Varanasi": {"lat": 25.3176, "lon": 82.9739, "state": "Uttar Pradesh", "zone": "North"},
    "Thiruvananthapuram": {"lat": 8.5241, "lon": 76.9366, "state": "Kerala", "zone": "South"},
    "Coimbatore": {"lat": 11.0168, "lon": 76.9558, "state": "Tamil Nadu", "zone": "South"},
    "Panaji": {"lat": 15.4909, "lon": 73.8278, "state": "Goa", "zone": "West"},
    "Leh": {"lat": 34.1526, "lon": 77.5771, "state": "Ladakh", "zone": "North"},
    "Raipur": {"lat": 21.2514, "lon": 81.6296, "state": "Chhattisgarh", "zone": "Central"},
    "Shillong": {"lat": 25.5788, "lon": 91.8933, "state": "Meghalaya", "zone": "Northeast"}
}

# Regional Climatic Plausibility Matrix (States allowed for specific extreme phenomena)
CLIMATIC_PLAUSIBILITY_RULES = {
    "Snowfall": [
        "Jammu and Kashmir", "Ladakh", "Himachal Pradesh", "Uttarakhand",
        "Sikkim", "Arunachal Pradesh"
    ],
    "Cyclone": [
        "Odisha", "Andhra Pradesh", "Tamil Nadu", "West Bengal", "Gujarat",
        "Maharashtra", "Kerala", "Goa", "Puducherry", "Andaman and Nicobar"
    ],
    "Dust Storm": [
        "Rajasthan", "Haryana", "Delhi", "Punjab", "Uttar Pradesh", "Gujarat", "Madhya Pradesh"
    ],
    "Heatwave": [
        "Rajasthan", "Delhi", "Uttar Pradesh", "Madhya Pradesh", "Gujarat",
        "Maharashtra", "Telangana", "Andhra Pradesh", "Bihar", "Odisha", "Punjab", "Haryana"
    ]
}
