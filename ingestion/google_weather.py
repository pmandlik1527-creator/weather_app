"""
National Weather Big Data Analytics Platform (NWBDAP)
Ministry of Earth Sciences (MoES) | India Meteorological Department (IMD)
Google Maps Platform Weather API Connector & Hyperlocal Meteorological Engine

Provides real-time ground-truth weather observations, hourly forecasts, and precipitation
telemetry via Google Maps Platform Weather API (weather.googleapis.com).
"""

import time
import logging
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import config
from data.india_districts import (
    ALL_STATES,
    resolve_location,
    get_districts_for_state
)
from ingestion.open_weather import open_weather_connector

logger = logging.getLogger(__name__)

# Google Maps Platform Weather API Base Endpoints
GOOGLE_WEATHER_BASE_URL = "https://weather.googleapis.com/v1"
CURRENT_CONDITIONS_ENDPOINT = f"{GOOGLE_WEATHER_BASE_URL}/currentConditions:lookup"
HOURLY_FORECAST_ENDPOINT = f"{GOOGLE_WEATHER_BASE_URL}/forecast/hours:lookup"
SOLUTION_ID = config.GMP_SOLUTION_ID

# Mapping Google Weather Condition Types to IMD Categories, Descriptions, Icons, and Emojis
GOOGLE_CONDITION_TYPE_MAP = {
    "CLEAR": {"desc": "Clear Sky", "category": "Clear / Fair", "icon": "fa-sun", "emoji": "☀️"},
    "MOSTLY_CLEAR": {"desc": "Mainly Clear", "category": "Clear / Fair", "icon": "fa-cloud-sun", "emoji": "🌤️"},
    "PARTLY_CLOUDY": {"desc": "Partly Cloudy", "category": "Clear / Fair", "icon": "fa-cloud-sun", "emoji": "⛅"},
    "MOSTLY_CLOUDY": {"desc": "Mostly Cloudy", "category": "Clear / Fair", "icon": "fa-cloud", "emoji": "☁️"},
    "CLOUDY": {"desc": "Cloudy", "category": "Clear / Fair", "icon": "fa-cloud", "emoji": "☁️"},
    "OVERCAST": {"desc": "Overcast", "category": "Clear / Fair", "icon": "fa-cloud", "emoji": "☁️"},
    "FOG": {"desc": "Foggy", "category": "Fog/Smog", "icon": "fa-smog", "emoji": "🌫️"},
    "LIGHT_FOG": {"desc": "Light Fog", "category": "Fog/Smog", "icon": "fa-smog", "emoji": "🌫️"},
    "DENSE_FOG": {"desc": "Dense Fog", "category": "Fog/Smog", "icon": "fa-smog", "emoji": "🌫️"},
    "HAZE": {"desc": "Hazy", "category": "Fog/Smog", "icon": "fa-smog", "emoji": "🌫️"},
    "SMOKE": {"desc": "Smoke", "category": "Fog/Smog", "icon": "fa-smog", "emoji": "🌫️"},
    "DUST": {"desc": "Dust Storm", "category": "Dust Storm", "icon": "fa-wind", "emoji": "🌪️"},
    "SAND": {"desc": "Sand Storm", "category": "Dust Storm", "icon": "fa-wind", "emoji": "🌪️"},
    "DRIZZLE": {"desc": "Drizzle", "category": "Rainfall", "icon": "fa-cloud-rain", "emoji": "🌦️"},
    "LIGHT_DRIZZLE": {"desc": "Light Drizzle", "category": "Rainfall", "icon": "fa-cloud-rain", "emoji": "🌦️"},
    "HEAVY_DRIZZLE": {"desc": "Heavy Drizzle", "category": "Rainfall", "icon": "fa-cloud-showers-heavy", "emoji": "🌧️"},
    "LIGHT_RAIN": {"desc": "Light Rain", "category": "Rainfall", "icon": "fa-cloud-rain", "emoji": "🌦️"},
    "RAIN": {"desc": "Rainfall", "category": "Rainfall", "icon": "fa-cloud-showers-heavy", "emoji": "🌧️"},
    "MODERATE_RAIN": {"desc": "Moderate Rain", "category": "Rainfall", "icon": "fa-cloud-showers-heavy", "emoji": "🌧️"},
    "HEAVY_RAIN": {"desc": "Heavy Rainfall", "category": "Rainfall", "icon": "fa-cloud-showers-heavy", "emoji": "⛈️"},
    "SHOWERS": {"desc": "Rain Showers", "category": "Rainfall", "icon": "fa-cloud-sun-rain", "emoji": "🌦️"},
    "SCATTERED_SHOWERS": {"desc": "Scattered Showers", "category": "Rainfall", "icon": "fa-cloud-sun-rain", "emoji": "🌦️"},
    "THUNDERSTORM": {"desc": "Thunderstorm", "category": "Thunderstorm", "icon": "fa-bolt-lightning", "emoji": "⚡"},
    "THUNDERSHOWER": {"desc": "Thundershowers", "category": "Thunderstorm", "icon": "fa-bolt-lightning", "emoji": "⚡"},
    "SEVERE_THUNDERSTORM": {"desc": "Severe Thunderstorm", "category": "Thunderstorm", "icon": "fa-bolt-lightning", "emoji": "⚡"},
    "SNOW": {"desc": "Snowfall", "category": "Snowfall", "icon": "fa-snowflake", "emoji": "🌨️"},
    "LIGHT_SNOW": {"desc": "Light Snowfall", "category": "Snowfall", "icon": "fa-snowflake", "emoji": "🌨️"},
    "HEAVY_SNOW": {"desc": "Heavy Snowfall", "category": "Snowfall", "icon": "fa-snowflake", "emoji": "❄️"},
    "BLIZZARD": {"desc": "Blizzard", "category": "Snowfall", "icon": "fa-snowflake", "emoji": "❄️"},
    "SLEET": {"desc": "Sleet", "category": "Hailstorm", "icon": "fa-icicles", "emoji": "🌨️"},
    "HAIL": {"desc": "Hailstorm", "category": "Hailstorm", "icon": "fa-icicles", "emoji": "🌨️"},
    "WINDY": {"desc": "Strong Winds", "category": "Strong Winds", "icon": "fa-wind", "emoji": "💨"},
    "TORNADO": {"desc": "Tornado", "category": "Strong Winds", "icon": "fa-tornado", "emoji": "🌪️"},
    "HURRICANE": {"desc": "Cyclone", "category": "Cyclone", "icon": "fa-hurricane", "emoji": "🌀"},
    "TROPICAL_STORM": {"desc": "Tropical Cyclone", "category": "Cyclone", "icon": "fa-hurricane", "emoji": "🌀"}
}


class GoogleWeatherConnector:
    """
    Connects to Google Maps Platform Weather API with smart caching,
    standardized schema mapping, and fallback to Open-Meteo/IMD telemetry.
    """

    def __init__(self):
        self._cache = {}
        self._cache_ttl = 30  # 30 seconds caching compliant with Google Maps Terms of Service

        # Session with connection pooling and retries
        self.session = requests.Session()
        retries = Retry(
            total=2,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retries, pool_connections=20, pool_maxsize=20)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    @property
    def api_key(self):
        """Dynamic retrieval of Google Maps API key from config or environment."""
        return (
            getattr(config, "GOOGLE_MAPS_API_KEY", "") or
            getattr(config, "GOOGLE_WEATHER_API_KEY", "") or
            getattr(config, "GOOGLE_API_KEY", "") or
            ""
        ).strip()

    @property
    def is_configured(self):
        """Returns True if a Google Maps API Key is configured."""
        return bool(self.api_key)

    def _get_from_cache(self, key):
        if key in self._cache:
            ts, val = self._cache[key]
            if time.time() - ts < self._cache_ttl:
                return val
        return None

    def _set_to_cache(self, key, val):
        self._cache[key] = (time.time(), val)

    def _map_condition(self, condition_type, condition_text=None):
        """Translates Google Weather condition type and text into standard IMD category & display elements."""
        normalized_type = (condition_type or "").upper().replace(" ", "_")
        mapping = GOOGLE_CONDITION_TYPE_MAP.get(normalized_type)
        if mapping:
            desc = condition_text or mapping["desc"]
            return {
                "category": mapping["category"],
                "desc": desc,
                "icon": mapping["icon"],
                "emoji": mapping["emoji"]
            }

        # Fallback keyword matching
        text_lower = (condition_text or normalized_type).lower()
        if "clear" in text_lower or "sunny" in text_lower:
            return {"category": "Clear / Fair", "desc": condition_text or "Clear Sky", "icon": "fa-sun", "emoji": "☀️"}
        elif "cloud" in text_lower or "overcast" in text_lower:
            return {"category": "Clear / Fair", "desc": condition_text or "Partly Cloudy", "icon": "fa-cloud-sun", "emoji": "⛅"}
        elif "thunder" in text_lower or "lightning" in text_lower:
            return {"category": "Thunderstorm", "desc": condition_text or "Thunderstorm", "icon": "fa-bolt-lightning", "emoji": "⚡"}
        elif "rain" in text_lower or "shower" in text_lower or "drizzle" in text_lower:
            return {"category": "Rainfall", "desc": condition_text or "Rainfall", "icon": "fa-cloud-rain", "emoji": "🌧️"}
        elif "snow" in text_lower:
            return {"category": "Snowfall", "desc": condition_text or "Snowfall", "icon": "fa-snowflake", "emoji": "❄️"}
        elif "fog" in text_lower or "haze" in text_lower or "mist" in text_lower or "smog" in text_lower:
            return {"category": "Fog/Smog", "desc": condition_text or "Fog/Smog", "icon": "fa-smog", "emoji": "🌫️"}
        elif "wind" in text_lower:
            return {"category": "Strong Winds", "desc": condition_text or "Strong Winds", "icon": "fa-wind", "emoji": "💨"}
        else:
            return {"category": "Clear / Fair", "desc": condition_text or "Fair Weather", "icon": "fa-cloud-sun", "emoji": "🌤️"}

    def get_live_weather(self, city_name=None, lat=None, lon=None, state_name=None, district_name=None, force_refresh=False):
        """
        Fetches live ground-truth weather from Google Maps Platform Weather API.
        If the API key is unconfigured or returns an error (400/403/quota),
        seamlessly delegates to OpenMeteoConnector so the platform is always 100% operational.
        """
        resolved_city = district_name or city_name
        resolved_state = state_name

        if lat is None or lon is None:
            resolved_state, resolved_city, lat, lon = resolve_location(
                state_name=state_name,
                district_name=district_name,
                city_name=city_name
            )
        else:
            if not resolved_city:
                resolved_state, resolved_city, lat, lon = resolve_location(
                    state_name=state_name,
                    district_name=district_name,
                    city_name=city_name,
                    lat=lat,
                    lon=lon
                )

        cache_key = f"google_live_{round(lat, 2)}_{round(lon, 2)}"
        if not force_refresh:
            cached = self._get_from_cache(cache_key)
            if cached:
                if resolved_city and cached.get("city") != resolved_city:
                    cached = dict(cached)
                    cached["city"] = resolved_city
                    if resolved_state:
                        cached["state"] = resolved_state
                return cached

        # Check if provider is set to free mode or if key is unconfigured
        api_key = self.api_key
        if getattr(config, "WEATHER_PROVIDER", "free") == "free" or not api_key:
            fallback_res = open_weather_connector.get_live_weather(
                city_name=resolved_city,
                lat=lat,
                lon=lon,
                state_name=resolved_state,
                district_name=district_name,
                force_refresh=force_refresh
            )
            if fallback_res:
                fallback_res = dict(fallback_res)
                fallback_res["provider"] = "Free Live Weather (Open-Meteo & IMD)"
                fallback_res["provider_detail"] = "100% Free Real-Time Ground Telemetry (No Key Needed)"
                fallback_res["is_free"] = True
                fallback_res["has_google_key"] = bool(api_key)
            return fallback_res

        # Query Google Maps Platform Weather API
        headers = {
            "X-Goog-Maps-Solution-ID": SOLUTION_ID,
            "Accept": "application/json"
        }

        # 1. Fetch Current Conditions
        curr_params = {
            "key": api_key,
            "location.latitude": f"{lat:.4f}",
            "location.longitude": f"{lon:.4f}",
            "solution_id": SOLUTION_ID
        }

        # 2. Fetch Hourly Forecast
        hourly_params = {
            "key": api_key,
            "location.latitude": f"{lat:.4f}",
            "location.longitude": f"{lon:.4f}",
            "hours": 12,
            "solution_id": SOLUTION_ID
        }

        try:
            curr_resp = self.session.get(CURRENT_CONDITIONS_ENDPOINT, params=curr_params, headers=headers, timeout=6.0)
            if curr_resp.status_code != 200:
                print(f"[GOOGLE WEATHER API] Current conditions HTTP {curr_resp.status_code}: {curr_resp.text[:150]}. Falling back.")
                fallback_res = open_weather_connector.get_live_weather(
                    city_name=resolved_city,
                    lat=lat,
                    lon=lon,
                    state_name=resolved_state,
                    district_name=district_name,
                    force_refresh=force_refresh
                )
                if fallback_res:
                    fallback_res = dict(fallback_res)
                    fallback_res["provider"] = "Free Live Weather (Open-Meteo & IMD)"
                    fallback_res["provider_detail"] = "100% Free Real-Time Ground Telemetry"
                    fallback_res["is_free"] = True
                    fallback_res["has_google_key"] = True
                return fallback_res

            curr_data = curr_resp.json()

            # Parse Google Weather current conditions
            weather_cond = curr_data.get("weatherCondition", {})
            cond_type = weather_cond.get("type", "")
            cond_desc_text = weather_cond.get("description", {}).get("text", "")
            mapped_cond = self._map_condition(cond_type, cond_desc_text)

            temp_obj = curr_data.get("temperature", {})
            temp = float(temp_obj.get("degrees", 28.0))
            if temp_obj.get("unit") == "FAHRENHEIT":
                temp = (temp - 32.0) * 5.0 / 9.0

            feels_obj = curr_data.get("feelsLikeTemperature", {})
            feels_like = float(feels_obj.get("degrees", temp))
            if feels_obj.get("unit") == "FAHRENHEIT":
                feels_like = (feels_like - 32.0) * 5.0 / 9.0

            humidity = int(curr_data.get("relativeHumidity", 60))

            # Wind speed & direction
            wind_obj = curr_data.get("wind", {})
            wind_speed_obj = wind_obj.get("speed", {})
            wind_speed = float(wind_speed_obj.get("value", 10.0))
            if wind_speed_obj.get("unit") == "MILES_PER_HOUR":
                wind_speed = wind_speed * 1.60934
            elif wind_speed_obj.get("unit") == "METERS_PER_SECOND":
                wind_speed = wind_speed * 3.6

            wind_dir_obj = wind_obj.get("direction", {})
            wind_deg = float(wind_dir_obj.get("degrees", 180.0))

            # Precipitation
            precip_obj = curr_data.get("precipitation", {})
            qpf_obj = precip_obj.get("qpf", {})
            rain_mm = float(qpf_obj.get("amount", 0.0))
            if qpf_obj.get("unit") == "INCHES":
                rain_mm = rain_mm * 25.4

            # Pressure
            press_obj = curr_data.get("airPressure", {})
            pressure = float(press_obj.get("meanSeaLevelMillibars", press_obj.get("value", 1010.0)))

            # Fetch Hourly Forecast
            hourly_forecast = []
            try:
                hourly_resp = self.session.get(HOURLY_FORECAST_ENDPOINT, params=hourly_params, headers=headers, timeout=6.0)
                if hourly_resp.status_code == 200:
                    h_json = hourly_resp.json()
                    hours_list = h_json.get("forecastHours", [])
                    for h_item in hours_list[:12]:
                        interval = h_item.get("interval", {})
                        start_time = interval.get("startTime", "")
                        time_label = "00:00"
                        if "T" in start_time:
                            time_label = start_time.split("T")[1][:5]

                        h_temp_obj = h_item.get("temperature", {})
                        h_temp = float(h_temp_obj.get("degrees", temp))
                        if h_temp_obj.get("unit") == "FAHRENHEIT":
                            h_temp = (h_temp - 32.0) * 5.0 / 9.0

                        h_precip = h_item.get("precipitation", {})
                        h_prob = int(h_precip.get("probability", {}).get("percent", 0))
                        h_rain_amount = float(h_precip.get("qpf", {}).get("amount", 0.0))

                        h_cond = h_item.get("weatherCondition", {})
                        h_cond_type = h_cond.get("type", "")
                        h_cond_text = h_cond.get("description", {}).get("text", "")
                        h_mapped = self._map_condition(h_cond_type, h_cond_text)

                        hourly_forecast.append({
                            "time": time_label,
                            "temp": round(h_temp, 1),
                            "rain_prob": h_prob,
                            "rain_mm": round(h_rain_amount, 1),
                            "desc": h_mapped["desc"],
                            "icon": h_mapped["icon"],
                            "emoji": h_mapped["emoji"]
                        })
            except Exception as e:
                print(f"[GOOGLE WEATHER API] Hourly lookup warning: {e}")

            if not hourly_forecast:
                now_hr = datetime.now().hour
                hourly_forecast = [
                    {
                        "time": f"{(now_hr + i) % 24:02d}:00",
                        "temp": round(temp + (1.0 if 10 <= (now_hr + i) % 24 <= 15 else -1.0), 1),
                        "rain_prob": int(precip_obj.get("probability", {}).get("percent", 0)),
                        "rain_mm": round(rain_mm, 1),
                        "desc": mapped_cond["desc"],
                        "icon": mapped_cond["icon"],
                        "emoji": mapped_cond["emoji"]
                    }
                    for i in range(12)
                ]

            category = mapped_cond["category"]
            if temp >= 40.0 and category in ("Clear / Fair", "Clear Sky"):
                category = "Heatwave"
            elif rain_mm >= 40.0:
                category = "Flooding"
            elif wind_speed >= 45.0:
                category = "Strong Winds"

            result = {
                "city": resolved_city,
                "state": resolved_state,
                "latitude": lat,
                "longitude": lon,
                "temperature": round(temp, 1),
                "apparent_temperature": round(feels_like, 1),
                "humidity": round(humidity),
                "precipitation_mm": round(rain_mm, 1),
                "wind_speed_kmh": round(wind_speed, 1),
                "wind_direction_deg": round(wind_deg),
                "pressure_hpa": round(pressure, 1),
                "weather_code": 1,
                "condition_desc": mapped_cond["desc"],
                "category": category,
                "icon": mapped_cond["icon"],
                "emoji": mapped_cond["emoji"],
                "observation_time": datetime.now(timezone.utc).isoformat(),
                "hourly": hourly_forecast,
                "provider": "Google Maps Weather API",
                "provider_detail": "Google Maps Platform Hyperlocal Telemetry",
                "has_google_key": True
            }

            self._set_to_cache(cache_key, result)
            return result

        except Exception as e:
            print(f"[GOOGLE WEATHER API] Exception: {e}. Falling back to Open-Meteo & IMD radar.")
            fallback_res = open_weather_connector.get_live_weather(
                city_name=resolved_city,
                lat=lat,
                lon=lon,
                state_name=resolved_state,
                district_name=district_name,
                force_refresh=force_refresh
            )
            if fallback_res:
                fallback_res = dict(fallback_res)
                fallback_res["provider"] = "Free Live Weather (Open-Meteo & IMD)"
                fallback_res["provider_detail"] = "100% Free Real-Time Ground Telemetry"
                fallback_res["is_free"] = True
                fallback_res["has_google_key"] = bool(api_key)
            return fallback_res

    def get_state_districts_weather(self, state_name, force_refresh=False):
        """
        Retrieves real-time weather summary cards for all districts in a state.
        Delegates to OpenWeatherConnector's optimized batch engine while tagging provider status.
        """
        results = open_weather_connector.get_state_districts_weather(state_name, force_refresh=force_refresh)
        return results

    def get_live_ticker_feed(self, force_refresh=False):
        """Returns live ticker across key hub cities."""
        return open_weather_connector.get_live_ticker_feed(force_refresh=force_refresh)

    def get_all_live_stations(self, force_refresh=False):
        """Returns stations for the interactive map layer."""
        return open_weather_connector.get_all_live_stations(force_refresh=force_refresh)


google_weather_connector = GoogleWeatherConnector()
