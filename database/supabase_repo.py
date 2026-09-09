"""
National Weather Big Data Analytics Platform (NWBDAP)
Supabase Cloud Repository Adapter
Executes cloud queries and synchronization with Supabase PostgreSQL.
"""

from datetime import datetime, timezone
from database.supabase_client import is_supabase_available, get_supabase_client
from database.repository import haversine_distance

def supabase_insert_report(report_data):
    """Inserts an enriched weather report into Supabase weather_reports table."""
    if not is_supabase_available():
        return None

    try:
        client = get_supabase_client()
        payload = {
            "report_uuid": report_data["report_uuid"],
            "source_type": report_data.get("source_type", "social_media"),
            "source_url": report_data.get("source_url", ""),
            "author_handle": report_data.get("author_handle", "anonymous"),
            "author_credibility_tier": report_data.get("author_credibility_tier", "social_public"),
            "source_credibility_score": float(report_data.get("source_credibility_score", 60.0)),
            "raw_text": report_data["raw_text"],
            "timestamp": report_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "latitude": report_data.get("latitude"),
            "longitude": report_data.get("longitude"),
            "city": report_data.get("city", "Unknown"),
            "state": report_data.get("state", "Unknown"),
            "detected_category": report_data.get("detected_category", "Rainfall"),
            "category_confidence": float(report_data.get("category_confidence", 0.8)),
            "is_fake": 1 if report_data.get("is_fake", False) else 0,
            "authenticity_score": float(report_data.get("authenticity_score", 85.0)),
            "fake_reasons": report_data.get("fake_reasons", []),
            "verification_status": report_data.get("verification_status", "unverified"),
            "severity_level": report_data.get("severity_level", "moderate"),
            "cluster_id": report_data.get("cluster_id"),
            "media_urls": report_data.get("media_urls", []),
            "citizen_contact": report_data.get("citizen_contact")
        }
        res = client.table("weather_reports").insert(payload).execute()
        if res.data and len(res.data) > 0:
            return res.data[0].get("id")
        return None
    except Exception as e:
        print(f"[SUPABASE REPO ERROR] Insert failed: {e}")
        return None

def supabase_query_reports(
    start_date=None,
    end_date=None,
    categories=None,
    state=None,
    city=None,
    status=None,
    source_type=None,
    is_fake=None,
    radius_lat=None,
    radius_lon=None,
    radius_km=None,
    limit=200,
    offset=0
):
    """Queries weather reports from Supabase with dynamic filters."""
    if not is_supabase_available():
        return None

    try:
        client = get_supabase_client()
        query = client.table("weather_reports").select("*")

        if start_date:
            query = query.gte("timestamp", start_date)
        if end_date:
            query = query.lte("timestamp", end_date)
        if categories and len(categories) > 0:
            query = query.in_("detected_category", categories)
        if state and state.strip() and state.lower() != "all":
            query = query.eq("state", state.strip())
        if city and city.strip() and city.lower() != "all":
            query = query.eq("city", city.strip())
        if status and status.strip() and status.lower() != "all":
            query = query.eq("verification_status", status.strip())
        if source_type and source_type.strip() and source_type.lower() != "all":
            query = query.eq("source_type", source_type.strip())
        if is_fake is not None:
            query = query.eq("is_fake", 1 if is_fake else 0)

        res = query.order("timestamp", desc=True).limit(limit).offset(offset).execute()
        rows = res.data or []

        results = []
        for item in rows:
            if radius_lat is not None and radius_lon is not None and radius_km is not None:
                dist = haversine_distance(
                    radius_lat, radius_lon, item.get("latitude"), item.get("longitude")
                )
                if dist > radius_km:
                    continue
                item["distance_km"] = round(dist, 2)
            results.append(item)

        return results
    except Exception as e:
        print(f"[SUPABASE REPO ERROR] Query failed: {e}")
        return None

def supabase_create_cluster(cluster_data):
    """Creates a new incident cluster in Supabase."""
    if not is_supabase_available():
        return None
    try:
        client = get_supabase_client()
        res = client.table("incident_clusters").insert(cluster_data).execute()
        if res.data and len(res.data) > 0:
            return res.data[0].get("id")
        return None
    except Exception as e:
        print(f"[SUPABASE REPO ERROR] Cluster create failed: {e}")
        return None

def supabase_get_active_clusters(limit=50):
    """Fetches active clusters from Supabase."""
    if not is_supabase_available():
        return None
    try:
        client = get_supabase_client()
        res = client.table("incident_clusters") \
            .select("*") \
            .eq("status", "active") \
            .order("report_count", desc=True) \
            .limit(limit) \
            .execute()
        return res.data or []
    except Exception as e:
        print(f"[SUPABASE REPO ERROR] Fetch active clusters failed: {e}")
        return None

def supabase_moderate_report(report_id, new_status, operator_name, notes=None, new_category=None):
    """Updates a report in Supabase and inserts audit log."""
    if not is_supabase_available():
        return None
    try:
        client = get_supabase_client()
        # Fetch existing
        curr = client.table("weather_reports").select("*").eq("id", report_id).execute()
        if not curr.data:
            return False
        report = curr.data[0]

        prev_status = report.get("verification_status")
        prev_cat = report.get("detected_category")
        final_cat = new_category if new_category else prev_cat
        is_fake_val = 1 if new_status in ("flagged_fake", "rejected") else 0

        # Update report
        client.table("weather_reports").update({
            "verification_status": new_status,
            "detected_category": final_cat,
            "is_fake": is_fake_val,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", report_id).execute()

        # Audit log
        client.table("moderation_audit_logs").insert({
            "report_id": report_id,
            "operator_name": operator_name,
            "action_type": "analyst_moderation",
            "previous_status": prev_status,
            "new_status": new_status,
            "previous_category": prev_cat,
            "new_category": final_cat,
            "notes": notes or ""
        }).execute()

        # Feedback log
        client.table("ml_feedback_log").insert({
            "report_id": report_id,
            "text_snippet": (report.get("raw_text") or "")[:250],
            "predicted_category": prev_cat,
            "corrected_category": final_cat,
            "was_fake_predicted": report.get("is_fake", 0),
            "was_fake_corrected": is_fake_val,
            "retrained_status": 0
        }).execute()

        return True
    except Exception as e:
        print(f"[SUPABASE REPO ERROR] Moderation failed: {e}")
        return False
