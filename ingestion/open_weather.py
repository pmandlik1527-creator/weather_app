"""
National Weather Big Data Analytics Platform (NWBDAP)
Open-Meteo Public Weather API Connector & Live Meteorological Engine
Provides real-time ground-truth observations, hourly forecasts, and national radar data.
"""

import time
import uuid
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import requests
import config
from ingestion.stream_manager import stream_pipeline

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Mapping Open-Meteo WMO weather codes to IMD Categories, Descriptions, and Icons
WMO_CODE_MAP = {
    0: {"desc": "Clear Sky", "category": "Heatwave", "icon": "fa-sun", "emoji": "☀️"},
    1: {"desc": "Mainly Clear", "category": "Heatwave", "icon": "fa-cloud-sun", "emoji": "🌤️"},
    2: {"desc": "Partly Cloudy", "category": "Rainfall", "icon": "fa-cloud-sun", "emoji": "⛅"},
    3: {"desc": "Overcast", "category": "Rainfall", "icon": "fa-cloud", "emoji": "☁️"},
    45: {"desc": "Foggy", "category": "Fog/Smog", "icon": "fa-smog", "emoji": "🌫️"},
    48: {"desc": "Depositing Rime Fog", "category": "Fog/Smog", "icon": "fa-smog", "emoji": "🌫️"},
    51: {"desc": "Light Drizzle", "category": "Rainfall", "icon": "fa-cloud-rain", "emoji": "🌦️"},
    53: {"desc": "Moderate Drizzle", "category": "Rainfall", "icon": "fa-cloud-rain", "emoji": "🌧️"},
    55: {"desc": "Dense Drizzle", "category": "Rainfall", "icon": "fa-cloud-showers-heavy", "emoji": "🌧️"},
    61: {"desc": "Slight Rain", "category": "Rainfall", "icon": "fa-cloud-rain", "emoji": "🌦️"},
    63: {"desc": "Moderate Rain", "category": "Rainfall", "icon": "fa-cloud-showers-heavy", "emoji": "🌧️"},
    65: {"desc": "Heavy Rainfall", "category": "Rainfall", "icon": "fa-cloud-showers-heavy", "emoji": "⛈️"},
    71: {"desc": "Slight Snowfall", "category": "Snowfall", "icon": "fa-snowflake", "emoji": "🌨️"},
    73: {"desc": "Moderate Snowfall", "category": "Snowfall", "icon": "fa-snowflake", "emoji": "❄️"},
    75: {"desc": "Heavy Snowfall", "category": "Snowfall", "icon": "fa-snowflake", "emoji": "❄️"},
    80: {"desc": "Rain Showers", "category": "Rainfall", "icon": "fa-cloud-sun-rain", "emoji": "🌦️"},
    81: {"desc": "Moderate Showers", "category": "Rainfall", "icon": "fa-cloud-showers-heavy", "emoji": "🌧️"},
    82: {"desc": "Violent Rain Showers", "category": "Flooding", "icon": "fa-water", "emoji": "🌊"},
    95: {"desc": "Thunderstorm", "category": "Thunderstorm", "icon": "fa-bolt-lightning", "emoji": "⚡"},
    96: {"desc": "Thunderstorm with Slight Hail", "category": "Hailstorm", "icon": "fa-icicles", "emoji": "🌨️"},
    99: {"desc": "Thunderstorm with Heavy Hail", "category": "Hailstorm", "icon": "fa-icicles", "emoji": "🌨️"},
}

class OpenWeatherConnector:
    """Connects to open meteorological observation feeds with smart memory caching."""

    def __init__(self):
        self.cities = config.MAJOR_INDIAN_CITIES
        self._cache = {}  # key -> (timestamp, data)
        self._cache_ttl = 300  # 5 minutes cache TTL

    def _get_from_cache(self, key):
        if key in self._cache:
            ts, val = self._cache[key]
            if time.time() - ts < self._cache_ttl:
                return val
        return None

    def _set_to_cache(self, key, val):
        self._cache[key] = (time.time(), val)

    def get_live_weather(self, city_name=None, lat=None, lon=None):
        """
        Fetches comprehensive real-time weather metrics for a city or arbitrary coordinates.
        Includes current observations and 24-hour hourly trend.
        """
        resolved_city = city_name
        resolved_state = "India"

        if city_name and city_name in self.cities:
            city_info = self.cities[city_name]
            lat = city_info["lat"]
            lon = city_info["lon"]
            resolved_state = city_info.get("state", "India")
        elif lat is not None and lon is not None:
            # Find nearest city name if not provided
            if not resolved_city:
                resolved_city = "Detected Location"
        else:
            # Default to New Delhi if unspecified
            resolved_city = "New Delhi"
            city_info = self.cities["New Delhi"]
            lat = city_info["lat"]
            lon = city_info["lon"]
            resolved_state = "Delhi"

        cache_key = f"live_{round(lat, 2)}_{round(lon, 2)}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,weather_code,surface_pressure,wind_speed_10m,wind_direction_10m",
            "hourly": "temperature_2m,precipitation_probability,weather_code",
            "timezone": "Asia/Kolkata",
            "forecast_days": 2
        }

        try:
            resp = requests.get(OPEN_METEO_URL, params=params, timeout=6.0)
            if resp.status_code != 200:
                return None

            data = resp.json()
            curr = data.get("current", {})
            hourly = data.get("hourly", {})

            wmo_code = curr.get("weather_code", 0)
            wmo_info = WMO_CODE_MAP.get(wmo_code, {
                "desc": "Fair Conditions", "category": "Rainfall", "icon": "fa-cloud-sun", "emoji": "⛅"
            })

            temp = curr.get("temperature_2m", 28.0)
            feels_like = curr.get("apparent_temperature", temp)
            humidity = curr.get("relative_humidity_2m", 60)
            rain = curr.get("rain", 0.0)
            wind_speed = curr.get("wind_speed_10m", 12.0)
            wind_deg = curr.get("wind_direction_10m", 180)
            pressure = curr.get("surface_pressure", 1010.0)

            # IMD category override
            category = wmo_info["category"]
            if temp >= 42.0:
                category = "Heatwave"
            elif rain >= 50.0:
                category = "Flooding"

            # Parse next 12-24 hours for hourly forecast strip
            hourly_forecast = []
            h_times = hourly.get("time", [])
            h_temps = hourly.get("temperature_2m", [])
            h_probs = hourly.get("precipitation_probability", [])
            h_codes = hourly.get("weather_code", [])

            # Find starting index close to current time
            curr_time_str = curr.get("time", "")
            start_idx = 0
            if curr_time_str and curr_time_str in h_times:
                start_idx = h_times.index(curr_time_str)

            for i in range(start_idx, min(start_idx + 12, len(h_times))):
                dt_str = h_times[i]
                hour_label = dt_str.split("T")[1] if "T" in dt_str else dt_str
                c = h_codes[i] if i < len(h_codes) else 0
                c_info = WMO_CODE_MAP.get(c, {"desc": "Normal", "emoji": "⛅", "icon": "fa-cloud"})
                hourly_forecast.append({
                    "time": hour_label,
                    "temp": round(h_temps[i], 1) if i < len(h_temps) else temp,
                    "rain_prob": h_probs[i] if i < len(h_probs) else 0,
                    "desc": c_info["desc"],
                    "icon": c_info["icon"],
                    "emoji": c_info["emoji"]
                })

            result = {
                "city": resolved_city,
                "state": resolved_state,
                "latitude": lat,
                "longitude": lon,
                "temperature": round(temp, 1),
                "apparent_temperature": round(feels_like, 1),
                "humidity": round(humidity),
                "precipitation_mm": round(rain, 1),
                "wind_speed_kmh": round(wind_speed, 1),
                "wind_direction_deg": round(wind_deg),
                "pressure_hpa": round(pressure, 1),
                "weather_code": wmo_code,
                "condition_desc": wmo_info["desc"],
                "category": category,
                "icon": wmo_info["icon"],
                "emoji": wmo_info["emoji"],
                "observation_time": curr.get("time", datetime.now(timezone.utc).isoformat()),
                "hourly": hourly_forecast
            }

            self._set_to_cache(cache_key, result)
            return result
        except Exception as e:
            print(f"[OPEN-METEO] Live fetch error: {e}")
            return None

    def get_live_ticker_feed(self):
        """Returns live conditions across key Indian hub cities for the top ticker strip."""
        cache_key = "ticker_feed"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        key_cities = [
            "New Delhi", "Mumbai", "Bengaluru", "Kolkata", 
            "Chennai", "Hyderabad", "Jaipur", "Shimla", 
            "Pune", "Guwahati", "Srinagar", "Ahmedabad"
        ]
        ticker_items = []
        with ThreadPoolExecutor(max_workers=6) as executor:
            future_to_city = {executor.submit(self.get_live_weather, city_name=c): c for c in key_cities}
            for future in future_to_city:
                try:
                    live = future.result(timeout=4.0)
                    if live:
                        ticker_items.append({
                            "city": live["city"],
                            "temp": live["temperature"],
                            "desc": live["condition_desc"],
                            "emoji": live["emoji"],
                            "icon": live["icon"],
                            "humidity": live["humidity"],
                            "wind": live["wind_speed_kmh"]
                        })
                except Exception:
                    pass

        if ticker_items:
            self._set_to_cache(cache_key, ticker_items)
        return ticker_items

    def get_all_live_stations(self):
        """Returns live observation data for all configured Indian stations for the map layer."""
        cache_key = "all_stations_layer"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        stations = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_city = {executor.submit(self.get_live_weather, city_name=c): c for c in self.cities.keys()}
            for future in future_to_city:
                try:
                    live = future.result(timeout=4.0)
                    if live:
                        stations.append({
                            "city": live["city"],
                            "state": live["state"],
                            "lat": live["latitude"],
                            "lon": live["longitude"],
                            "temp": live["temperature"],
                            "feels_like": live["apparent_temperature"],
                            "humidity": live["humidity"],
                            "rain": live["precipitation_mm"],
                            "wind": live["wind_speed_kmh"],
                            "desc": live["condition_desc"],
                            "category": live["category"],
                            "icon": live["icon"],
                            "emoji": live["emoji"]
                        })
                except Exception:
                    pass

        if stations:
            self._set_to_cache(cache_key, stations)
        return stations

    def fetch_station_observation(self, city_name):
        """
        Legacy/streaming connector method: polls station and pushes report into
        the streaming ingestion priority queue.
        """
        live = self.get_live_weather(city_name=city_name)
        if not live:
            return None

        city_data = self.cities.get(city_name, {})
        text = (
            f"Official Ground Station Observation [{city_name}]: {live['condition_desc']} {live['emoji']}. "
            f"Temp: {live['temperature']}°C (Feels like {live['apparent_temperature']}°C), "
            f"Humidity: {live['humidity']}%, Rain: {live['precipitation_mm']}mm, "
            f"Wind: {live['wind_speed_kmh']} km/h. Automated ground-truth telemetry."
        )

        severity = "mild"
        if live['precipitation_mm'] > 25.0 or live['wind_speed_kmh'] > 50.0 or live['temperature'] > 43.0:
            severity = "severe"
        elif live['precipitation_mm'] > 10.0 or live['wind_speed_kmh'] > 30.0 or live['temperature'] > 40.0:
            severity = "moderate"

        report_dict = {
            "report_uuid": f"METEO-{uuid.uuid4().hex[:10].upper()}",
            "source_type": "open_meteo",
            "source_id": "open_meteo_imd",
            "source_url": "https://open-meteo.com",
            "author_handle": "@Indiametdept",
            "raw_text": text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": city_data.get("lat"),
            "longitude": city_data.get("lon"),
            "city": city_name,
            "state": city_data.get("state", "India"),
            "severity_level": severity,
            "media_urls": []
        }

        stream_pipeline.push_raw_report(report_dict)
        return report_dict

    def sync_all_major_stations(self):
        """Polls top key meteorological nodes into the platform stream queue."""
        key_stations = ["New Delhi", "Mumbai", "Bengaluru", "Kolkata", "Chennai", "Hyderabad", "Jaipur", "Pune"]
        synced = 0
        for city in key_stations:
            res = self.fetch_station_observation(city)
            if res:
                synced += 1
        return synced

open_weather_connector = OpenWeatherConnector()
