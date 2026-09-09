"""
National Weather Big Data Analytics Platform (NWBDAP)
Citizen Weather Reporting Intake Handler
Validates, geocodes, and queues direct citizen submissions.
"""

import uuid
from datetime import datetime, timezone
import config
from database.repository import haversine_distance
from ingestion.stream_manager import stream_pipeline

def find_nearest_indian_city(lat, lon):
    """Finds the closest known Indian city/state based on GPS coordinates."""
    if lat is None or lon is None:
        return "New Delhi", "Delhi"

    best_city = "New Delhi"
    best_state = "Delhi"
    min_dist = float("inf")

    for city_name, meta in config.MAJOR_INDIAN_CITIES.items():
        dist = haversine_distance(lat, lon, meta["lat"], meta["lon"])
        if dist < min_dist:
            min_dist = dist
            best_city = city_name
            best_state = meta["state"]

    return best_city, best_state

class CitizenReportHandler:
    """Handles intake of ground-level citizen crowd reports."""

    def process_submission(self, form_data):
        """
        Validates and enqueues a citizen submission.
        Parameters:
            form_data (dict): Citizen form payload.
        Returns:
            dict: { 'success': bool, 'report_uuid': str, 'message': str }
        """
        raw_text = form_data.get("description", "").strip()
        if not raw_text or len(raw_text) < 5:
            return {"success": False, "message": "Weather description is too short (minimum 5 characters)."}

        # Latitude & Longitude
        try:
            lat = float(form_data.get("latitude")) if form_data.get("latitude") else None
            lon = float(form_data.get("longitude")) if form_data.get("longitude") else None
        except (ValueError, TypeError):
            lat, lon = None, None

        city = form_data.get("city", "").strip()
        state = form_data.get("state", "").strip()

        # Auto-match city/state if missing but coordinates exist
        if (not city or not state) and lat is not None and lon is not None:
            resolved_city, resolved_state = find_nearest_indian_city(lat, lon)
            city = city or resolved_city
            state = state or resolved_state

        city = city or "Unknown"
        state = state or "Unknown"

        severity = form_data.get("severity", "moderate").lower()
        if severity not in ["mild", "moderate", "severe", "extreme"]:
            severity = "moderate"

        citizen_name = form_data.get("citizen_name", "Anonymous Citizen").strip()
        contact = form_data.get("citizen_contact", "").strip()
        media_urls = form_data.get("media_urls", [])

        # If user uploaded a photo simulation/URL
        photo_url = form_data.get("photo_url")
        if photo_url and photo_url not in media_urls:
            media_urls.append(photo_url)

        report_uuid = f"CTZ-{uuid.uuid4().hex[:10].upper()}"

        report_dict = {
            "report_uuid": report_uuid,
            "source_type": "citizen",
            "source_id": "citizen_portal",
            "source_url": "/report",
            "author_handle": citizen_name or "@citizen_reporter",
            "citizen_contact": contact,
            "raw_text": raw_text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": lat,
            "longitude": lon,
            "city": city,
            "state": state,
            "severity_level": severity,
            "media_urls": media_urls
        }

        # Push to asynchronous streaming queue
        queued = stream_pipeline.push_raw_report(report_dict)

        if queued:
            return {
                "success": True,
                "report_uuid": report_uuid,
                "city": city,
                "state": state,
                "message": "Citizen weather report successfully received and queued for IMD verification."
            }
        else:
            return {
                "success": False,
                "message": "Pipeline buffer busy. Please try submitting again in a moment."
            }

citizen_handler = CitizenReportHandler()
