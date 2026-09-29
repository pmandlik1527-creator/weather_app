"""
National Weather Big Data Analytics Platform (NWBDAP)
Ministry of Earth Sciences (MoES) | India Meteorological Department (IMD)
OpenRouter AI Weather Forecast & Meteorological Intelligence Engine

Generates deep AI-driven weather synopses, multi-hour risk forecasts,
hazard warnings, and public safety advisories using OpenRouter LLMs.
"""

import time
import json
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import config

logger = logging.getLogger(__name__)

OPENROUTER_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"

class OpenRouterForecastService:
    """
    Connects to OpenRouter to analyze live ground-truth meteorological telemetry
    and produce human-readable AI forecasts, risk classifications, and advisories.
    """

    def __init__(self):
        self._cache = {}  # key -> (timestamp, data)
        self._cache_ttl = 300  # 5 minutes caching to save tokens and minimize latency

        self.session = requests.Session()
        retries = Retry(
            total=2,
            backoff_factor=0.4,
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    @property
    def api_key(self):
        return getattr(config, "OPENROUTER_API_KEY", "").strip()

    @property
    def model_name(self):
        return getattr(config, "OPENROUTER_MODEL", "google/gemini-2.5-flash").strip()

    def _get_from_cache(self, key):
        if key in self._cache:
            ts, val = self._cache[key]
            if time.time() - ts < self._cache_ttl:
                return val
        return None

    def _set_to_cache(self, key, val):
        self._cache[key] = (time.time(), val)

    def generate_weather_forecast(self, weather_data, force_refresh=False):
        """
        Takes real-time weather metrics dict and generates structured AI analysis.
        Returns:
            dict containing summary, hazard_level, badge, key_hazards, advisories, synoptic_analysis, and meta.
        """
        if not weather_data:
            return None

        city = weather_data.get("city", "Unknown City")
        state = weather_data.get("state", "India")
        temp = weather_data.get("temperature", 28.0)
        feels_like = weather_data.get("apparent_temperature", temp)
        humidity = weather_data.get("humidity", 60)
        rain = weather_data.get("precipitation_mm", 0.0)
        wind = weather_data.get("wind_speed_kmh", 10.0)
        pressure = weather_data.get("pressure_hpa", 1010.0)
        condition = weather_data.get("condition_desc", "Fair")
        category = weather_data.get("category", "Clear / Fair")
        hourly = weather_data.get("hourly", [])[:8]

        cache_key = f"ai_fc_{city.lower()}_{state.lower()}"
        if not force_refresh:
            cached = self._get_from_cache(cache_key)
            if cached:
                cached_res = dict(cached)
                cached_res["cached"] = True
                return cached_res

        # If OpenRouter API Key is configured, query OpenRouter LLM
        if self.api_key:
            ai_result = self._call_openrouter_api(
                city=city,
                state=state,
                temp=temp,
                feels_like=feels_like,
                humidity=humidity,
                rain=rain,
                wind=wind,
                pressure=pressure,
                condition=condition,
                category=category,
                hourly=hourly
            )
            if ai_result:
                self._set_to_cache(cache_key, ai_result)
                return ai_result

        # Intelligent meteorological fallback if API key is not yet set or during network hiccup
        fallback = self._generate_intelligent_fallback(
            city=city,
            state=state,
            temp=temp,
            feels_like=feels_like,
            humidity=humidity,
            rain=rain,
            wind=wind,
            pressure=pressure,
            condition=condition,
            category=category,
            hourly=hourly
        )
        self._set_to_cache(cache_key, fallback)
        return fallback

    def _call_openrouter_api(self, city, state, temp, feels_like, humidity, rain, wind, pressure, condition, category, hourly):
        """Dispatches structured prompt to OpenRouter endpoint."""
        hourly_summary = ", ".join([f"{h.get('time', '')}: {h.get('temp', '')}°C ({h.get('rain_prob', 0)}% rain, {h.get('desc', '')})" for h in hourly])

        system_prompt = (
            "You are the Senior Chief Meteorologist for the India Meteorological Department (IMD) / Ministry of Earth Sciences. "
            "Analyze live sensor telemetry and provide a sharp, authoritative meteorological forecast briefing. "
            "You MUST respond ONLY with valid JSON conforming to this schema:\n"
            "{\n"
            '  "summary": "2-3 sentences executive meteorological forecast synopsis for the next 12-24 hours.",\n'
            '  "hazard_level": "Low" | "Moderate" | "High" | "Severe",\n'
            '  "hazard_badge": "🟢 Normal / Favorable" | "🟡 Moderate Advisory" | "🟠 Severe Warning" | "🔴 Critical Alert",\n'
            '  "key_hazards": ["List of 2-3 specific weather risks or atmospheric concerns"],\n'
            '  "advisories": ["List of 2-3 actionable citizen/travel/farming recommendations"],\n'
            '  "synoptic_analysis": "1-2 sentences on barometric pressure dynamics, moisture advection, or thermal trends."\n'
            "}"
        )

        user_content = (
            f"Location: {city}, {state}, India\n"
            f"Current Conditions: {condition} ({category})\n"
            f"Temperature: {temp}°C (Apparent: {feels_like}°C)\n"
            f"Relative Humidity: {humidity}%\n"
            f"Precipitation: {rain} mm\n"
            f"Wind Speed: {wind} km/h\n"
            f"Atmospheric Pressure: {pressure} hPa\n"
            f"Hourly Micro-Forecast: {hourly_summary}\n\n"
            "Provide the expert IMD meteorological analysis in exact JSON format."
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": getattr(config, "OPENROUTER_SITE_URL", "https://wataveran.onrender.com"),
            "X-Title": getattr(config, "OPENROUTER_SITE_NAME", "IMD NWBDAP Weather Platform"),
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.3,
            "max_tokens": 450,
            "response_format": {"type": "json_object"}
        }

        try:
            resp = self.session.post(OPENROUTER_COMPLETIONS_URL, headers=headers, json=payload, timeout=12.0)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    content_str = choices[0].get("message", {}).get("content", "").strip()
                    # Clean potential markdown fences
                    if content_str.startswith("```json"):
                        content_str = content_str[7:]
                    if content_str.startswith("```"):
                        content_str = content_str[3:]
                    if content_str.endswith("```"):
                        content_str = content_str[:-3]
                    content_str = content_str.strip()

                    parsed = json.loads(content_str)
                    return {
                        "status": "success",
                        "provider": "OpenRouter",
                        "model": self.model_name,
                        "is_live_ai": True,
                        "summary": parsed.get("summary", ""),
                        "hazard_level": parsed.get("hazard_level", "Low"),
                        "hazard_badge": parsed.get("hazard_badge", "🟢 Normal Conditions"),
                        "key_hazards": parsed.get("key_hazards", []),
                        "advisories": parsed.get("advisories", []),
                        "synoptic_analysis": parsed.get("synoptic_analysis", ""),
                        "cached": False,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S IST")
                    }
            else:
                logger.warning(f"[OPENROUTER] API returned status {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"[OPENROUTER] Request error: {e}")

        return None

    def _generate_intelligent_fallback(self, city, state, temp, feels_like, humidity, rain, wind, pressure, condition, category, hourly):
        """
        High-fidelity rule-based meteorological forecast generator.
        Activates when OPENROUTER_API_KEY is not configured or offline, ensuring
        zero UI failure and realistic IMD meteorological advisory outputs.
        """
        is_configured = bool(self.api_key)

        # Assess hazard levels based on meteorological thresholds
        if rain >= 35.0 or wind >= 45.0 or temp >= 42.0:
            hazard_level = "Severe"
            hazard_badge = "🔴 Critical Meteorological Alert"
        elif rain >= 15.0 or wind >= 30.0 or temp >= 39.0 or humidity >= 88:
            hazard_level = "High"
            hazard_badge = "🟠 Elevated Weather Warning"
        elif rain >= 2.0 or wind >= 20.0 or temp >= 35.0:
            hazard_level = "Moderate"
            hazard_badge = "🟡 Moderate Advisory"
        else:
            hazard_level = "Low"
            hazard_badge = "🟢 Favorable Atmospheric Conditions"

        # Determine specific hazards and advisories
        hazards = []
        advisories = []

        if temp >= 38.0:
            hazards.append(f"Elevated thermal stress with apparent temperature reaching {round(feels_like, 1)}°C")
            advisories.append("Avoid prolonged direct sun exposure during peak hours (12:00 - 15:30); stay hydrated")
        elif temp <= 10.0:
            hazards.append("Low ambient temperatures with wind chill effects during early morning hours")
            advisories.append("Adequate warm attire recommended for outdoor commutes")

        if rain >= 10.0:
            hazards.append(f"Significant precipitation accumulation ({rain} mm) with potential localized waterlogging")
            advisories.append("Allow extra transit time and navigate with caution around low-lying roadways")
        elif rain > 0.0:
            hazards.append("Intermittent rain showers resulting in slick road surfaces and reduced visibility")
            advisories.append("Keep rain gear handy; exercise caution while driving")
        else:
            if humidity >= 80:
                hazards.append("High relative humidity creating sultry atmospheric conditions")
            else:
                hazards.append("Normal diurnal atmospheric cycle with stable thermodynamic equilibrium")

        if wind >= 25.0:
            hazards.append(f"Gusty wind velocities up to {round(wind, 1)} km/h")
            advisories.append("Secure temporary outdoor hoardings and lightweight structures")

        if not advisories:
            advisories.append("Atmospheric conditions favorable for standard transit and outdoor operations")
            advisories.append("No adverse meteorological disruption anticipated over the immediate 12-hour window")

        # Generate summary
        summary = (
            f"Atmospheric conditions over {city}, {state} indicate {condition.lower()} with current temperature at {round(temp, 1)}°C "
            f"(feels like {round(feels_like, 1)}°C) and {humidity}% relative humidity. "
            f"Over the next 12 hours, barometric pressure ({round(pressure, 1)} hPa) and wind velocity ({round(wind, 1)} km/h) "
            f"point towards {category.lower()} conditions prevailing across the district."
        )

        synoptic = (
            f"Surface boundary layer stability remains consistent with barometric pressure at {round(pressure, 1)} hPa. "
            f"Moisture index stands at {humidity}%, maintaining stable local convection patterns."
        )

        return {
            "status": "success",
            "provider": "OpenRouter (Meteorological Engine)" if not is_configured else "OpenRouter (Local Fallback)",
            "model": self.model_name if is_configured else "IMD-Meteorological-Rules (Set OPENROUTER_API_KEY for Live LLM)",
            "is_live_ai": False,
            "summary": summary,
            "hazard_level": hazard_level,
            "hazard_badge": hazard_badge,
            "key_hazards": hazards,
            "advisories": advisories,
            "synoptic_analysis": synoptic,
            "cached": False,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S IST"),
            "needs_api_key": not is_configured
        }

openrouter_forecast_service = OpenRouterForecastService()
