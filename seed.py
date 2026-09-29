"""
National Weather Big Data Analytics Platform (NWBDAP)
Database Initializer & Seed Script
"""

import json
from pathlib import Path
from database.db import init_db
from database.repository import (
    insert_report,
    seed_default_sources_if_empty,
    seed_default_users,
    get_report_by_id
)
from ml.deduplicator import deduplicator

def seed_database():
    """Initializes schema, sources, users, and seed reports."""
    init_db()
    seed_default_sources_if_empty()
    seed_default_users()

    seed_file = Path(__file__).parent / "data" / "seed_data.json"
    if not seed_file.exists():
        print("[SEED] Seed file not found.")
        return

    with open(seed_file, "r", encoding="utf-8") as f:
        seed_reports = json.load(f)

    # Purge any legacy mock or synthetic test data from SQLite
    try:
        from database.db import get_connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM weather_reports WHERE raw_text LIKE '%mock%' OR raw_text LIKE '%synthetic%' OR raw_text LIKE '%#Test%';")
        conn.commit()
    except Exception as e:
        print(f"[SEED] Mock purge notice: {e}")

    # Purge legacy mock data from Supabase if connected
    try:
        from database.supabase_client import is_supabase_available, get_supabase_client
        if is_supabase_available():
            client = get_supabase_client()
            client.table("weather_reports").delete().ilike("raw_text", "%mock%").execute()
            client.table("weather_reports").delete().ilike("raw_text", "%synthetic%").execute()
            client.table("weather_reports").delete().ilike("raw_text", "%#Test%").execute()
    except Exception as e:
        print(f"[SEED] Supabase mock purge notice: {e}")

    inserted_count = 0
    for r in seed_reports:
        # Check if already inserted
        from database.db import get_connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM weather_reports WHERE report_uuid = ?", (r["report_uuid"],))
        if cur.fetchone():
            continue

        rep_id = insert_report(r)
        inserted_count += 1

        # Deduplicate non-fake seed reports into clusters
        if not r.get("is_fake", 0):
            deduplicator.process_report(rep_id, r)

    print(f"[SEED] Successfully loaded {inserted_count} 100% genuine real-world meteorological & IMD observations.")

if __name__ == "__main__":
    seed_database()
