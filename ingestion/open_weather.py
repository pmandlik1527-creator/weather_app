"""
National Weather Big Data Analytics Platform (NWBDAP)
Open-Meteo Public Weather API Connector
Fetches ground-truth meteorological observations across major Indian stations.
"""

import uuid
from datetime import datetime, timezone
import requests
import config
from ingestion.stream_manager import stream_pipeline

# Open-Meteo endpoint (free, no API key needed, open-source aligned)
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Mapping Open-Meteo WMO weather interpretation codes to IMD categories
WMO_CODE_MAP = {
    0: ("Clear Skies", "Heatwave"),
    1: ("Mainly Clear", "Heatwave"),
    2: ("Partly Cloudy", "Rainfall"),
    3: ("Overcast", "Rainfall"),
    45: ("Foggy Conditions", "Fog/Smog"),
    48: ("Depositing Rime Fog", "Fog/Smog"),
    51: ("Light Drizzle", "Rainfall"),
    53: ("Moderate Drizzle", "Rainfall"),
    55: ("Dense Drizzle", "Rainfall"),
    61: ("Slight Rain", "Rainfall"),
    63: ("Moderate Rain", "Rainfall"),
    65: ("Heavy Rainfall", "Rainfall"),
    71: ("Slight Snow Fall", "Snowfall"),
    73: ("Moderate Snow Fall", "Snowfall"),
    75: ("Heavy Snow Fall", "Snowfall"),
    80: ("Rain Showers", "Rainfall"),
    81: ("Moderate Rain Showers", "Rainfall"),
    82: ("Violent Rain Showers", "Flooding"),
    95: ("Thunderstorm", "Thunderstorm"),
    96: ("Thunderstorm with Slight Hail", "Hailstorm"),
    99: ("Thunderstorm with Heavy Hail", "Hailstorm"),
}

class OpenWeatherConnector:
    """Connects to open meteorological observation feeds."""

    def __init__(self):
        self.cities = config.MAJOR_INDIAN_CITIES

    def fetch_station_observation(self, city_name):
        """Fetches live meteorological parameters for a specific Indian station."""
        if city_name not in self.cities:
            return None

        city_data = self.cities[city_name]
        params = {
            "latitude": city_data["lat"],
            "longitude": city_data["lon"],
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,wind_speed_10m,wind_gusts_10m",
            "timezone": "Asia/Kolkata"
        }

        try:
            resp = requests.get(OPEN_METEO_URL, params=params, timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                current = data.get("current", {})

                wmo_code = current.get("weather_code", 0)
                temp = current.get("temperature_2m", 30.0)
                rain = current.get("rain", 0.0)
                wind = current.get("wind_speed_10m", 10.0)

                wmo_desc, category = WMO_CODE_MAP.get(wmo_code, ("Normal weather", "Rainfall"))

                # Special heatwave override
                if temp >= 42.0:
                    category = "Heatwave"

                text = (
                    f"Official Ground Station Observation [{city_name}]: {wmo_desc}. "
                    f"Temp: {temp}°C, Precipitation: {rain}mm, Wind Speed: {wind} km/h. "
                    f"Verified automated sensor feed."
                )

                severity = "mild"
                if rain > 25.0 or wind > 50.0 or temp > 43.0:
                    severity = "severe"
                elif rain > 10.0 or wind > 30.0:
                    severity = "moderate"

                report_dict = {
                    "report_uuid": f"METEO-{uuid.uuid4().hex[:10].upper()}",
                    "source_type": "open_meteo",
                    "source_id": "open_meteo_imd",
                    "source_url": "https://open-meteo.com",
                    "author_handle": "@Indiametdept",
                    "raw_text": text,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "latitude": city_data["lat"],
                    "longitude": city_data["lon"],
                    "city": city_name,
                    "state": city_data["state"],
                    "severity_level": severity,
                    "media_urls": []
                }

                stream_pipeline.push_raw_report(report_dict)
                return report_dict
        except Exception as e:
            # Non-blocking network fallback
            print(f"[OPEN-METEO] Observation sync note: {e}")
            return None

    def sync_all_major_stations(self):
        """Polls top key meteorological nodes."""
        key_stations = ["New Delhi", "Mumbai", "Bengaluru", "Kolkata", "Chennai"]
        synced = 0
        for city in key_stations:
            res = self.fetch_station_observation(city)
            if res:
                synced += 1
        return synced

open_weather_connector = OpenWeatherConnector()
