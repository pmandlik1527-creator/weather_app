"""
National Weather Big Data Analytics Platform (NWBDAP)
Supabase Client Connection Manager
Provides unified cloud PostgreSQL access via Supabase REST API.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()

_supabase_client = None
_is_connected = False

def init_supabase():
    """Initializes the Supabase client if valid credentials exist."""
    global _supabase_client, _is_connected

    if not SUPABASE_URL or not SUPABASE_KEY:
        _is_connected = False
        return None

    if not SUPABASE_URL.startswith("http") or "your-project-ref" in SUPABASE_URL:
        _is_connected = False
        return None

    try:
        from supabase import create_client, ClientOptions
        _supabase_client = create_client(
            SUPABASE_URL,
            SUPABASE_KEY,
            options=ClientOptions(postgrest_client_timeout=10)
        )
        # Verify connectivity by pinging sources_config or weather_reports
        _ = _supabase_client.table("sources_config").select("id").limit(1).execute()
        _is_connected = True
        print(f"[SUPABASE] Successfully connected to Supabase Cloud at {SUPABASE_URL}")
        return _supabase_client
    except Exception as e:
        print(f"[SUPABASE NOTE] Could not connect to Supabase: {e}")
        print("[SUPABASE NOTE] Falling back seamlessly to local SQLite WAL mode.")
        _is_connected = False
        return None

def is_supabase_available():
    """Returns True if Supabase is configured and reachable."""
    global _is_connected
    if _supabase_client is None and SUPABASE_URL and SUPABASE_KEY:
        init_supabase()
    return _is_connected

def get_supabase_client():
    """Returns the active Supabase client instance, or None if offline."""
    global _supabase_client
    if _supabase_client is None:
        init_supabase()
    return _supabase_client

# Attempt initial connection
init_supabase()
