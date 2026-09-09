"""
National Weather Big Data Analytics Platform (NWBDAP)
Ministry of Earth Sciences (MoES) | India Meteorological Department (IMD)
Launcher Script
"""

import sys
import config
from app import app

if __name__ == "__main__":
    print("=" * 70)
    print(" MINISTRY OF EARTH SCIENCES (MoES) | GOVT OF INDIA")
    print(" INDIA METEOROLOGICAL DEPARTMENT (IMD)")
    print(" National Weather Big Data Analytics Platform (NWBDAP)")
    print(" Problem Statement ID: 26069 | Smart India Hackathon")
    print("=" * 70)
    print(f" * Database Path    : {config.DB_PATH}")
    print(f" * Server Listening : http://localhost:{config.PORT}")
    print(f" * Operational Radar: http://localhost:{config.PORT}/")
    print(f" * Citizen Desk     : http://localhost:{config.PORT}/report")
    print(f" * Admin Moderation : http://localhost:{config.PORT}/admin")
    print(f" * Big Data Trends  : http://localhost:{config.PORT}/analytics")
    print("=" * 70)

    try:
        app.run(host=config.HOST, port=config.PORT, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n[NWBDAP] Graceful shutdown.")
        sys.exit(0)
