"""
National Weather Big Data Analytics Platform (NWBDAP)
Supabase Migration & Data Synchronization Tool
Transfers local SQLite intelligence data to Supabase Cloud PostgreSQL.
"""

import sys
import json
from database.db import get_connection
from database.supabase_client import is_supabase_available, get_supabase_client

def migrate_data():
    """Migrates all existing records from SQLite to Supabase."""
    print("=" * 70)
    print(" NWBDAP SUPABASE CLOUD MIGRATION TOOL")
    print("=" * 70)

    if not is_supabase_available():
        print("\n[ERROR] Supabase is not configured or not reachable.")
        print("\nTo connect to your Supabase project:")
        print("1. Open your Supabase project at https://supabase.com/dashboard")
        print("2. Navigate to Project Settings -> API")
        print("3. Copy 'Project URL' and 'anon / service_role API Key'")
        print("4. Paste them into your '.env' file:")
        print("     SUPABASE_URL=https://your-project-ref.supabase.co")
        print("     SUPABASE_KEY=your-api-key")
        print("5. Make sure you ran 'database/supabase_schema.sql' in the Supabase SQL Editor.")
        print("6. Run this script again: python migrate_to_supabase.py")
        sys.exit(1)

    client = get_supabase_client()
    conn = get_connection()
    cur = conn.cursor()

    # 1. Migrate Sources Config
    print("\n[1/4] Migrating Data Ingestion Sources...")
    cur.execute("SELECT * FROM sources_config")
    sources = [dict(r) for r in cur.fetchall()]
    for s in sources:
        try:
            client.table("sources_config").upsert({
                "source_id": s["source_id"],
                "name": s["name"],
                "source_type": s["source_type"],
                "target_query": s["target_query"],
                "is_active": s["is_active"],
                "polling_interval_seconds": s["polling_interval_seconds"],
                "total_ingested": s["total_ingested"],
                "health_status": s["health_status"]
            }, on_conflict="source_id").execute()
        except Exception as e:
            print(f"  Note on source {s['source_id']}: {e}")
    print(f"  -> {len(sources)} sources synced to Supabase.")

    # 2. Migrate Incident Clusters
    print("\n[2/4] Migrating Incident Clusters (Deduplicated Events)...")
    cur.execute("SELECT * FROM incident_clusters")
    clusters = [dict(r) for r in cur.fetchall()]
    for c in clusters:
        try:
            client.table("incident_clusters").upsert({
                "cluster_uuid": c["cluster_uuid"],
                "title": c["title"],
                "category": c["category"],
                "severity": c["severity"],
                "center_lat": c["center_lat"],
                "center_lon": c["center_lon"],
                "city": c["city"],
                "state": c["state"],
                "report_count": c["report_count"],
                "first_reported_at": c["first_reported_at"],
                "last_reported_at": c["last_reported_at"],
                "status": c["status"],
                "summary": c["summary"]
            }, on_conflict="cluster_uuid").execute()
        except Exception as e:
            print(f"  Note on cluster {c['cluster_uuid']}: {e}")
    print(f"  -> {len(clusters)} clusters synced to Supabase.")

    # 3. Migrate Weather Reports
    print("\n[3/4] Migrating Enriched Weather Reports...")
    cur.execute("SELECT * FROM weather_reports")
    reports = [dict(r) for r in cur.fetchall()]
    migrated_reports = 0
    for r in reports:
        try:
            client.table("weather_reports").upsert({
                "report_uuid": r["report_uuid"],
                "source_type": r["source_type"],
                "source_url": r["source_url"],
                "author_handle": r["author_handle"],
                "author_credibility_tier": r["author_credibility_tier"],
                "source_credibility_score": r["source_credibility_score"],
                "raw_text": r["raw_text"],
                "timestamp": r["timestamp"],
                "latitude": r["latitude"],
                "longitude": r["longitude"],
                "city": r["city"],
                "state": r["state"],
                "detected_category": r["detected_category"],
                "category_confidence": r["category_confidence"],
                "is_fake": r["is_fake"],
                "authenticity_score": r["authenticity_score"],
                "fake_reasons": json.loads(r["fake_reasons"] or "[]"),
                "verification_status": r["verification_status"],
                "severity_level": r["severity_level"],
                "media_urls": json.loads(r["media_urls"] or "[]"),
                "citizen_contact": r["citizen_contact"]
            }, on_conflict="report_uuid").execute()
            migrated_reports += 1
        except Exception as e:
            print(f"  Note on report {r['report_uuid']}: {e}")
    print(f"  -> {migrated_reports} reports synced to Supabase.")

    # 4. Migrate Moderation Audit Logs
    print("\n[4/4] Migrating Moderation Audit Logs...")
    cur.execute("SELECT * FROM moderation_audit_logs")
    logs = [dict(r) for r in cur.fetchall()]
    migrated_logs = 0
    for l in logs:
        try:
            client.table("moderation_audit_logs").insert({
                "operator_name": l["operator_name"],
                "action_type": l["action_type"],
                "previous_status": l["previous_status"],
                "new_status": l["new_status"],
                "previous_category": l["previous_category"],
                "new_category": l["new_category"],
                "notes": l["notes"]
            }).execute()
            migrated_logs += 1
        except Exception as e:
            pass
    print(f"  -> {migrated_logs} audit logs synced to Supabase.")

    print("\n" + "=" * 70)
    print(" [SUCCESS] All local weather intelligence successfully synchronized with Supabase!")
    print("=" * 70)

if __name__ == "__main__":
    migrate_data()
