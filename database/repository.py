"""
National Weather Big Data Analytics Platform (NWBDAP)
Data Access Repository
"""

import json
import math
from datetime import datetime, timedelta, timezone
from database.db import db_cursor, get_connection
import config

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in kilometers between two GPS coordinates using Haversine formula."""
    if None in (lat1, lon1, lat2, lon2):
        return float('inf')
    R = 6371.0 # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# --- Reports ---

def insert_report(report_data):
    """Inserts an enriched weather report into the database."""
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO weather_reports (
                report_uuid, source_type, source_url, author_handle,
                author_credibility_tier, source_credibility_score,
                raw_text, timestamp, latitude, longitude, city, state,
                detected_category, category_confidence, is_fake,
                authenticity_score, fake_reasons, verification_status,
                severity_level, cluster_id, media_urls, citizen_contact,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            report_data["report_uuid"],
            report_data.get("source_type", "social_media"),
            report_data.get("source_url", ""),
            report_data.get("author_handle", "anonymous"),
            report_data.get("author_credibility_tier", "social_public"),
            float(report_data.get("source_credibility_score", 60.0)),
            report_data["raw_text"],
            report_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            report_data.get("latitude"),
            report_data.get("longitude"),
            report_data.get("city", "Unknown"),
            report_data.get("state", "Unknown"),
            report_data.get("detected_category", "Rainfall"),
            float(report_data.get("category_confidence", 0.8)),
            1 if report_data.get("is_fake", False) else 0,
            float(report_data.get("authenticity_score", 85.0)),
            json.dumps(report_data.get("fake_reasons", [])),
            report_data.get("verification_status", "unverified"),
            report_data.get("severity_level", "moderate"),
            report_data.get("cluster_id"),
            json.dumps(report_data.get("media_urls", [])),
            report_data.get("citizen_contact")
        ))
        last_id = cur.lastrowid

    # Cloud sync to Supabase if connected
    try:
        from database.supabase_repo import supabase_insert_report
        supabase_insert_report(report_data)
    except Exception:
        pass

    return last_id

def get_report_by_id(report_id):
    """Fetches a single report by ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM weather_reports WHERE id = ?", (report_id,))
    row = cur.fetchone()
    if not row:
        return None
    data = dict(row)
    data["fake_reasons"] = json.loads(data["fake_reasons"] or "[]")
    data["media_urls"] = json.loads(data["media_urls"] or "[]")
    return data

def query_reports(
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
    """Queries weather reports with multi-criteria dynamic filtering."""
    # Attempt Supabase query if connected
    try:
        from database.supabase_client import is_supabase_available
        if is_supabase_available():
            from database.supabase_repo import supabase_query_reports
            supa_results = supabase_query_reports(
                start_date=start_date, end_date=end_date, categories=categories,
                state=state, city=city, status=status, source_type=source_type,
                is_fake=is_fake, radius_lat=radius_lat, radius_lon=radius_lon,
                radius_km=radius_km, limit=limit, offset=offset
            )
            if supa_results is not None and len(supa_results) > 0:
                return supa_results
    except Exception:
        pass

    conn = get_connection()
    cur = conn.cursor()

    conditions = ["1=1"]
    params = []

    if start_date:
        conditions.append("timestamp >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("timestamp <= ?")
        params.append(end_date)
    if categories and len(categories) > 0:
        placeholders = ",".join(["?"] * len(categories))
        conditions.append(f"detected_category IN ({placeholders})")
        params.extend(categories)
    if state and state.strip() and state.lower() != "all":
        conditions.append("state = ?")
        params.append(state.strip())
    if city and city.strip() and city.lower() != "all":
        conditions.append("city = ?")
        params.append(city.strip())
    if status and status.strip() and status.lower() != "all":
        conditions.append("verification_status = ?")
        params.append(status.strip())
    if source_type and source_type.strip() and source_type.lower() != "all":
        conditions.append("source_type = ?")
        params.append(source_type.strip())
    if is_fake is not None:
        conditions.append("is_fake = ?")
        params.append(1 if is_fake else 0)

    where_clause = " AND ".join(conditions)
    query = f"""
        SELECT * FROM weather_reports
        WHERE {where_clause}
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    cur.execute(query, params)
    rows = cur.fetchall()

    results = []
    for r in rows:
        item = dict(r)
        item["fake_reasons"] = json.loads(item["fake_reasons"] or "[]")
        item["media_urls"] = json.loads(item["media_urls"] or "[]")

        # Radius filter if coordinates provided
        if radius_lat is not None and radius_lon is not None and radius_km is not None:
            dist = haversine_distance(
                radius_lat, radius_lon, item.get("latitude"), item.get("longitude")
            )
            if dist > radius_km:
                continue
            item["distance_km"] = round(dist, 2)

        results.append(item)

    return results

def get_nearby_recent_reports(lat, lon, max_dist_km, max_hours_ago):
    """Finds reports within a radius and time window for corroboration and deduplication."""
    conn = get_connection()
    cur = conn.cursor()
    cutoff_time = (datetime.now(timezone.utc) - timedelta(hours=max_hours_ago)).isoformat()

    cur.execute("""
        SELECT * FROM weather_reports
        WHERE timestamp >= ?
        AND latitude IS NOT NULL
        AND longitude IS NOT NULL
        ORDER BY timestamp DESC
        LIMIT 200
    """, (cutoff_time,))

    rows = cur.fetchall()
    matches = []
    for r in rows:
        item = dict(r)
        dist = haversine_distance(lat, lon, item["latitude"], item["longitude"])
        if dist <= max_dist_km:
            item["distance_km"] = dist
            matches.append(item)
    return matches

# --- Incident Clusters (Deduplication) ---

def create_cluster(cluster_data):
    """Creates a new incident cluster."""
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO incident_clusters (
                cluster_uuid, title, category, severity, center_lat, center_lon,
                city, state, report_count, first_reported_at, last_reported_at,
                status, summary, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            cluster_data["cluster_uuid"],
            cluster_data["title"],
            cluster_data["category"],
            cluster_data.get("severity", "moderate"),
            cluster_data["center_lat"],
            cluster_data["center_lon"],
            cluster_data["city"],
            cluster_data["state"],
            cluster_data.get("report_count", 1),
            cluster_data["first_reported_at"],
            cluster_data["last_reported_at"],
            cluster_data.get("status", "active"),
            cluster_data.get("summary", "")
        ))
        last_id = cur.lastrowid

    # Cloud sync to Supabase if connected
    try:
        from database.supabase_repo import supabase_create_cluster
        supabase_create_cluster(cluster_data)
    except Exception:
        pass

    return last_id

def update_cluster_increment(cluster_id, report_timestamp, new_lat=None, new_lon=None):
    """Increments report count on an incident cluster and updates last reported time."""
    with db_cursor() as cur:
        cur.execute("""
            UPDATE incident_clusters
            SET report_count = report_count + 1,
                last_reported_at = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (report_timestamp, cluster_id))

def get_active_clusters(limit=50):
    """Fetches currently active incident clusters."""
    try:
        from database.supabase_client import is_supabase_available
        if is_supabase_available():
            from database.supabase_repo import supabase_get_active_clusters
            supa_clusters = supabase_get_active_clusters(limit=limit)
            if supa_clusters is not None and len(supa_clusters) > 0:
                return supa_clusters
    except Exception:
        pass

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM incident_clusters
        WHERE status = 'active'
        ORDER BY report_count DESC, last_reported_at DESC
        LIMIT ?
    """, (limit,))
    return [dict(r) for r in cur.fetchall()]

def assign_report_to_cluster(report_id, cluster_id):
    """Assigns an individual report to a cluster."""
    with db_cursor() as cur:
        cur.execute("""
            UPDATE weather_reports
            SET cluster_id = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (cluster_id, report_id))

# --- Moderation & Audit ---

def moderate_report(report_id, new_status, operator_name, notes=None, new_category=None):
    """Updates a report's verification status, logs audit entry, and records ML feedback."""
    report = get_report_by_id(report_id)
    if not report:
        return False

    prev_status = report["verification_status"]
    prev_category = report["detected_category"]
    final_category = new_category if new_category else prev_category
    is_fake_val = 1 if new_status in ("flagged_fake", "rejected") else 0

    with db_cursor() as cur:
        cur.execute("""
            UPDATE weather_reports
            SET verification_status = ?,
                detected_category = ?,
                is_fake = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (new_status, final_category, is_fake_val, report_id))

        # Insert audit log
        cur.execute("""
            INSERT INTO moderation_audit_logs (
                report_id, operator_name, action_type,
                previous_status, new_status,
                previous_category, new_category,
                notes, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            report_id, operator_name, "analyst_moderation",
            prev_status, new_status,
            prev_category, final_category,
            notes or ""
        ))

        # Insert ML feedback log if status changed or category was corrected
        cur.execute("""
            INSERT INTO ml_feedback_log (
                report_id, text_snippet, predicted_category, corrected_category,
                was_fake_predicted, was_fake_corrected, retrained_status, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, 0, datetime('now'))
        """, (
            report_id,
            report["raw_text"][:250],
            prev_category,
            final_category,
            report["is_fake"],
            is_fake_val
        ))

    # Cloud sync to Supabase if connected
    try:
        from database.supabase_repo import supabase_moderate_report
        supabase_moderate_report(report_id, new_status, operator_name, notes, final_category)
    except Exception:
        pass

    return True

def get_audit_logs(limit=50):
    """Fetches recent moderation audit logs."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.*, r.raw_text, r.city, r.state, r.author_handle
        FROM moderation_audit_logs a
        JOIN weather_reports r ON a.report_id = r.id
        ORDER BY a.timestamp DESC
        LIMIT ?
    """, (limit,))
    return [dict(r) for r in cur.fetchall()]

# --- Analytics & Summary Queries ---

def get_analytics_summary(days=7):
    """Computes comprehensive analytics metrics for the dashboard."""
    conn = get_connection()
    cur = conn.cursor()

    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    # Total counts
    cur.execute("""
        SELECT
            COUNT(*) as total_reports,
            SUM(CASE WHEN is_fake = 1 THEN 1 ELSE 0 END) as fake_count,
            SUM(CASE WHEN verification_status = 'verified' THEN 1 ELSE 0 END) as verified_count,
            SUM(CASE WHEN verification_status = 'unverified' THEN 1 ELSE 0 END) as unverified_count,
            SUM(CASE WHEN verification_status = 'flagged_fake' THEN 1 ELSE 0 END) as flagged_count,
            AVG(authenticity_score) as avg_authenticity,
            AVG(source_credibility_score) as avg_credibility
        FROM weather_reports
        WHERE timestamp >= ?
    """, (cutoff_date,))
    totals = dict(cur.fetchone() or {})

    # Active clusters
    cur.execute("SELECT COUNT(*) as active_cluster_count FROM incident_clusters WHERE status = 'active'")
    cluster_stat = cur.fetchone()
    totals["active_cluster_count"] = cluster_stat["active_cluster_count"] if cluster_stat else 0

    # Category distribution
    cur.execute("""
        SELECT detected_category, COUNT(*) as count
        FROM weather_reports
        WHERE timestamp >= ?
        GROUP BY detected_category
        ORDER BY count DESC
    """, (cutoff_date,))
    categories = [dict(r) for r in cur.fetchall()]

    # State hotspots
    cur.execute("""
        SELECT state, COUNT(*) as count,
               SUM(CASE WHEN is_fake = 1 THEN 1 ELSE 0 END) as fake_count
        FROM weather_reports
        WHERE timestamp >= ? AND state != 'Unknown'
        GROUP BY state
        ORDER BY count DESC
        LIMIT 10
    """, (cutoff_date,))
    state_hotspots = [dict(r) for r in cur.fetchall()]

    # Source platform breakdown
    cur.execute("""
        SELECT source_type, COUNT(*) as count,
               AVG(source_credibility_score) as avg_credibility
        FROM weather_reports
        WHERE timestamp >= ?
        GROUP BY source_type
        ORDER BY count DESC
    """, (cutoff_date,))
    source_breakdown = [dict(r) for r in cur.fetchall()]

    # Timeline trends (by day or hour)
    cur.execute("""
        SELECT substr(timestamp, 1, 10) as date_str,
               COUNT(*) as total_count,
               SUM(CASE WHEN is_fake = 1 THEN 1 ELSE 0 END) as fake_count,
               SUM(CASE WHEN verification_status = 'verified' THEN 1 ELSE 0 END) as verified_count
        FROM weather_reports
        WHERE timestamp >= ?
        GROUP BY date_str
        ORDER BY date_str ASC
    """, (cutoff_date,))
    timeline = [dict(r) for r in cur.fetchall()]

    return {
        "totals": totals,
        "categories": categories,
        "state_hotspots": state_hotspots,
        "source_breakdown": source_breakdown,
        "timeline": timeline
    }

# --- Sources Config ---

def get_sources_config():
    """Lists all configured ingestion sources."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM sources_config ORDER BY id ASC")
    return [dict(r) for r in cur.fetchall()]

def toggle_source_status(source_id, is_active):
    """Enables or disables an ingestion source."""
    with db_cursor() as cur:
        cur.execute("""
            UPDATE sources_config
            SET is_active = ?
            WHERE source_id = ?
        """, (1 if is_active else 0, source_id))

def increment_source_ingested(source_id, count=1):
    """Increments the count of ingested items for a source."""
    with db_cursor() as cur:
        cur.execute("""
            UPDATE sources_config
            SET total_ingested = total_ingested + ?,
                last_poll_at = datetime('now')
            WHERE source_id = ?
        """, (count, source_id))

def seed_default_sources_if_empty():
    """Seeds default social media hashtag feeds and API sources."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as count FROM sources_config")
    if cur.fetchone()["count"] == 0:
        default_sources = [
            ("tw_imd_official", "Twitter / X #IMD & Weather Tags", "twitter", "#IMD,#IndiaWeather,#Monsoon,#DelhiRains", 1, 5),
            ("tw_mumbai_rains", "Twitter / X #MumbaiRains Stream", "twitter", "#MumbaiRains,#MumbaiFloods", 1, 5),
            ("tw_cyclone_watch", "Twitter / X Cyclone Alerts", "twitter", "#CycloneAlert,#BayOfBengal", 1, 10),
            ("citizen_portal", "Citizen Web & Mobile Reporting Desk", "citizen", "direct_submission_api", 1, 1),
            ("open_meteo_imd", "Open-Meteo Ground Observation Sensors", "open_meteo", "national_radar_grid", 1, 30),
            ("ig_weather_photos", "Instagram Weather Stories & Photos", "instagram", "#weatherindia,#monsoondairies", 1, 15)
        ]
        with db_cursor() as wcur:
            for s_id, name, stype, query, active, poll in default_sources:
                wcur.execute("""
                    INSERT INTO sources_config (source_id, name, source_type, target_query, is_active, polling_interval_seconds)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (s_id, name, stype, query, active, poll))
        print("[DB] Default data sources seeded.")
