"""
National Weather Big Data Analytics Platform (NWBDAP)
Ministry of Earth Sciences (MoES) | India Meteorological Department (IMD)
Problem Statement ID: 26069
Core Flask Application & REST API
"""

import io
import csv
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, jsonify, Response, send_file, session, redirect, url_for, flash
import config
from database.db import init_db
from database.repository import (
    query_reports,
    get_report_by_id,
    get_active_clusters,
    get_analytics_summary,
    moderate_report,
    get_audit_logs,
    get_sources_config,
    toggle_source_status,
    seed_default_sources_if_empty,
    create_user,
    get_user_by_id,
    get_user_by_username_or_email,
    authenticate_user
)
from ingestion.stream_manager import stream_pipeline
from ingestion.social_connector import social_connector
from ingestion.open_weather import open_weather_connector
from ingestion.citizen_handler import citizen_handler
from ml.feedback import feedback_manager
from seed import seed_database
from data.india_districts import (
    ALL_STATES,
    INDIA_STATES_DISTRICTS,
    DISTRICT_SUGGESTIONS,
    get_all_states,
    get_districts_for_state,
    resolve_location
)

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

# ==========================================
# Authentication & Authorization Helpers
# ==========================================

def get_current_user():
    """Returns the authenticated user dict or None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_user_by_id(user_id)

@app.context_processor
def inject_current_user():
    """Makes current_user available to all Jinja2 templates."""
    return {"current_user": get_current_user()}

def login_required(f):
    """Decorator ensuring user is authenticated."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required", "authenticated": False}), 401
            return redirect(url_for("login_view", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    """Decorator ensuring user has an allowed role (e.g. admin, meteorologist)."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Authentication required", "authenticated": False}), 401
                return redirect(url_for("login_view", next=request.url))
            if user.get("role") not in allowed_roles:
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Forbidden: insufficient permissions"}), 403
                flash("Access restricted to authorized IMD personnel.", "error")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Ensure DB is seeded on app startup
try:
    seed_database()
    stream_pipeline.start()
except Exception as e:
    print(f"[STARTUP WARN] {e}")

# ==========================================
# Web Page Routes
# ==========================================

@app.route("/")
def index():
    """Main IMD Meteorologist Analytics Dashboard."""
    summary = get_analytics_summary()
    initial_state = request.args.get("state", "Maharashtra")
    initial_district = request.args.get("district") or request.args.get("city", "Pune")
    initial_weather = open_weather_connector.get_live_weather(
        state_name=initial_state,
        district_name=initial_district
    )

    districts_by_state = {
        st: [d["name"] for d in get_districts_for_state(st)]
        for st in ALL_STATES
    }

    return render_template(
        "index.html",
        categories=config.WEATHER_CATEGORIES,
        all_states=ALL_STATES,
        districts_by_state=districts_by_state,
        district_suggestions=DISTRICT_SUGGESTIONS,
        initial_state=initial_weather.get("state", initial_state),
        initial_district=initial_weather.get("city", initial_district),
        initial_weather=initial_weather,
        summary=summary
    )

@app.route("/report")
def citizen_portal():
    """Citizen Weather Reporting Portal."""
    return render_template(
        "citizen.html",
        categories=config.WEATHER_CATEGORIES,
        cities=sorted(list(config.MAJOR_INDIAN_CITIES.keys())),
        states=sorted(list(set(c["state"] for c in config.MAJOR_INDIAN_CITIES.values())))
    )

# ==========================================
# Authentication & User Management Routes
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login_view():
    """Authentication portal for IMD Officers and Citizens."""
    if session.get("user_id"):
        return redirect(request.args.get("next") or url_for("index"))

    error = None
    tab = request.args.get("tab", "login")

    if request.method == "POST":
        identifier = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = authenticate_user(identifier, password)
        if user:
            session.permanent = remember
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash(f"Welcome back, {user['full_name']}!", "success")
            next_page = request.args.get("next")
            if next_page and not next_page.startswith("//") and not "://" in next_page:
                return redirect(next_page)
            if user["role"] in ("admin", "meteorologist"):
                return redirect(url_for("admin_panel"))
            return redirect(url_for("index"))
        else:
            error = "Invalid username or password. Please verify your credentials."

    return render_template("login.html", error=error, tab=tab)

@app.route("/register", methods=["GET", "POST"])
def register_view():
    """Registration portal for Citizens and Field Observers."""
    if session.get("user_id"):
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        full_name = request.form.get("full_name", "").strip()
        designation = request.form.get("designation", "").strip()

        if password != confirm_password:
            error = "Passwords do not match."
        elif len(password) < 6:
            error = "Password must be at least 6 characters long."
        else:
            try:
                user = create_user(
                    username=username,
                    email=email,
                    password=password,
                    full_name=full_name,
                    role="citizen",
                    designation=designation
                )
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["role"] = user["role"]
                flash(f"Account created successfully! Welcome, {user['full_name']}.", "success")
                next_page = request.args.get("next")
                if next_page and not next_page.startswith("//") and not "://" in next_page:
                    return redirect(next_page)
                return redirect(url_for("index"))
            except ValueError as ve:
                error = str(ve)
            except Exception as e:
                error = f"Registration failed: {str(e)}"

    return render_template("login.html", error=error, tab="register")

@app.route("/logout")
def logout():
    """Terminates active user session."""
    session.clear()
    flash("You have been securely signed out.", "info")
    return redirect(url_for("index"))

@app.route("/api/auth/me", methods=["GET"])
def api_auth_me():
    """Returns profile for currently authenticated user."""
    user = get_current_user()
    if user:
        return jsonify({"authenticated": True, "user": user})
    return jsonify({"authenticated": False, "user": None})

@app.route("/admin")
@role_required(["admin", "meteorologist"])
def admin_panel():
    """IMD Administrator & Moderation Panel."""
    sources = get_sources_config()
    telemetry = stream_pipeline.get_telemetry()
    ml_stats = feedback_manager.get_model_performance_stats()
    return render_template(
        "admin.html",
        sources=sources,
        telemetry=telemetry,
        ml_stats=ml_stats,
        categories=config.WEATHER_CATEGORIES
    )

@app.route("/analytics")
def analytics_view():
    """Dedicated Analytics & Big Data Deep Dive."""
    summary = get_analytics_summary(days=30)
    return render_template("analytics.html", summary=summary)

# ==========================================
# REST API Endpoints
# ==========================================

@app.route("/api/reports", methods=["GET"])
def api_reports():
    """Query weather reports with multi-criteria dynamic filtering."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    categories_raw = request.args.get("categories")
    categories = [c.strip() for c in categories_raw.split(",") if c.strip()] if categories_raw else None
    state = request.args.get("state")
    city = request.args.get("city")
    status = request.args.get("status")
    source_type = request.args.get("source_type")

    is_fake_raw = request.args.get("is_fake")
    is_fake = None
    if is_fake_raw in ("1", "true", "True"):
        is_fake = True
    elif is_fake_raw in ("0", "false", "False"):
        is_fake = False

    # Radius search parameters
    try:
        radius_lat = float(request.args.get("lat")) if request.args.get("lat") else None
        radius_lon = float(request.args.get("lon")) if request.args.get("lon") else None
        radius_km = float(request.args.get("radius_km")) if request.args.get("radius_km") else None
    except (ValueError, TypeError):
        radius_lat, radius_lon, radius_km = None, None, None

    limit = min(int(request.args.get("limit", 200)), 1000)
    offset = int(request.args.get("offset", 0))

    reports = query_reports(
        start_date=start_date,
        end_date=end_date,
        categories=categories,
        state=state,
        city=city,
        status=status,
        source_type=source_type,
        is_fake=is_fake,
        radius_lat=radius_lat,
        radius_lon=radius_lon,
        radius_km=radius_km,
        limit=limit,
        offset=offset
    )

    return jsonify({"count": len(reports), "reports": reports})

@app.route("/api/report/<int:report_id>", methods=["GET"])
def api_single_report(report_id):
    """Retrieve detailed report metadata by ID."""
    report = get_report_by_id(report_id)
    if not report:
        return jsonify({"error": "Report not found"}), 404
    return jsonify(report)

@app.route("/api/report/submit", methods=["POST"])
def api_citizen_submit():
    """Intake endpoint for citizen crowdsourced weather reports."""
    data = request.get_json(silent=True) or request.form.to_dict()
    res = citizen_handler.process_submission(data)
    return jsonify(res), (200 if res.get("success") else 400)

@app.route("/api/clusters", methods=["GET"])
def api_clusters():
    """Retrieve active deduplicated incident clusters."""
    limit = int(request.args.get("limit", 50))
    clusters = get_active_clusters(limit=limit)
    return jsonify({"count": len(clusters), "clusters": clusters})

@app.route("/api/analytics", methods=["GET"])
def api_analytics():
    """Retrieve aggregated dashboard analytics metrics."""
    days = int(request.args.get("days", 7))
    summary = get_analytics_summary(days=days)
    return jsonify(summary)

@app.route("/api/telemetry", methods=["GET"])
def api_telemetry():
    """Returns live ingestion and streaming pipeline telemetry."""
    stats = stream_pipeline.get_telemetry()
    stats["is_social_streaming"] = social_connector.is_streaming
    return jsonify(stats)

# ==========================================
# Streaming & Ingestion Simulation Controls
# ==========================================

@app.route("/api/stream/start", methods=["POST"])
def api_start_stream():
    """Starts live social media hashtag simulation."""
    data = request.get_json(silent=True) or {}
    interval = float(data.get("interval", config.SIMULATION_STREAM_INTERVAL_SECONDS))
    social_connector.start_stream(interval)
    return jsonify({"success": True, "message": f"Stream activated at {interval}s interval."})

@app.route("/api/stream/stop", methods=["POST"])
def api_stop_stream():
    """Pauses live social media hashtag simulation."""
    social_connector.stop_stream()
    return jsonify({"success": True, "message": "Stream paused."})

@app.route("/api/stream/pulse", methods=["POST"])
def api_stream_pulse():
    """Emits an immediate single weather report into the live queue."""
    report = social_connector.emit_single_report()
    return jsonify({"success": True, "emitted": report})

@app.route("/api/stream/sync-meteo", methods=["POST"])
def api_sync_meteo():
    """Polls live ground truth observations from Open-Meteo API for Indian stations."""
    count = open_weather_connector.sync_all_major_stations()
    return jsonify({"success": True, "synced_stations": count})

@app.route("/api/social/sync-live-imd", methods=["POST"])
def api_sync_live_imd():
    """Crawls and ingests up-to-the-minute real-world #IMD and weather social posts."""
    limit = int(request.args.get("limit") or (request.get_json(silent=True) or {}).get("limit", 15))
    posts = social_connector.fetch_live_imd_social_posts(limit=limit)
    return jsonify({
        "success": True,
        "count": len(posts),
        "message": f"Successfully ingested {len(posts)} live #IMD social media posts.",
        "posts": posts
    })

@app.route("/api/social/ingest", methods=["POST"])
def api_ingest_custom_post():
    """Allows ingesting and classifying an arbitrary custom Tweet / social post."""
    data = request.get_json(silent=True) or request.form.to_dict()
    if not data or not data.get("text"):
        return jsonify({"success": False, "error": "Post text is required."}), 400

    try:
        report = social_connector.ingest_custom_social_post(
            raw_text=data.get("text"),
            author_handle=data.get("author_handle"),
            source_url=data.get("source_url"),
            platform=data.get("platform", "twitter"),
            media_urls=data.get("media_urls")
        )
        return jsonify({
            "success": True,
            "message": "Social media post analyzed and ingested successfully.",
            "report": report
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

# ==========================================
# Real-Time Live Meteorological Endpoints
# ==========================================

@app.route("/api/weather/live", methods=["GET"])
def api_live_weather():
    """Returns real-time ground-truth weather observations and 24h hourly forecast for any state/district or coordinates."""
    state = request.args.get("state")
    district = request.args.get("district")
    city = request.args.get("city")
    lat_val = request.args.get("lat")
    lon_val = request.args.get("lon")

    lat = float(lat_val) if lat_val else None
    lon = float(lon_val) if lon_val else None

    data = open_weather_connector.get_live_weather(
        city_name=city,
        lat=lat,
        lon=lon,
        state_name=state,
        district_name=district
    )
    if not data:
        return jsonify({"error": "Unable to fetch live weather telemetry."}), 502
    return jsonify({"success": True, "data": data})

@app.route("/api/weather/states", methods=["GET"])
def api_weather_states():
    """Returns all 36 Indian states/UTs and their districts."""
    districts_by_state = {
        st: [d["name"] for d in get_districts_for_state(st)]
        for st in ALL_STATES
    }
    return jsonify({
        "success": True,
        "states": ALL_STATES,
        "districts_by_state": districts_by_state,
        "suggestions": DISTRICT_SUGGESTIONS
    })

@app.route("/api/weather/state-summary", methods=["GET"])
def api_weather_state_summary():
    """Returns live weather overview for all districts in a given state."""
    state = request.args.get("state", "Maharashtra")
    districts_weather = open_weather_connector.get_state_districts_weather(state)
    return jsonify({
        "success": True,
        "state": state,
        "districts": districts_weather,
        "count": len(districts_weather)
    })

@app.route("/api/weather/ticker", methods=["GET"])
def api_weather_ticker():
    """Returns live conditions across key Indian hub cities for the top ticker strip."""
    ticker_data = open_weather_connector.get_live_ticker_feed()
    return jsonify({"success": True, "ticker": ticker_data})

@app.route("/api/weather/stations", methods=["GET"])
def api_weather_stations():
    """Returns real-time observations for all Indian stations for map overlay."""
    stations = open_weather_connector.get_all_live_stations()
    return jsonify({"success": True, "stations": stations})


# ==========================================
# Admin & Moderation Controls
# ==========================================

@app.route("/api/admin/sources", methods=["GET"])
def api_admin_sources():
    """Lists configured data sources."""
    sources = get_sources_config()
    return jsonify(sources)

@app.route("/api/admin/source/toggle", methods=["POST"])
@role_required(["admin", "meteorologist"])
def api_toggle_source():
    """Enables or disables an ingestion source."""
    data = request.get_json(silent=True) or {}
    source_id = data.get("source_id")
    is_active = bool(data.get("is_active"))
    if not source_id:
        return jsonify({"error": "source_id is required"}), 400
    toggle_source_status(source_id, is_active)
    return jsonify({"success": True, "source_id": source_id, "is_active": is_active})

@app.route("/api/admin/moderate", methods=["POST"])
@role_required(["admin", "meteorologist"])
def api_moderate_report():
    """Human-in-the-loop analyst review and override."""
    data = request.get_json(silent=True) or {}
    report_id = data.get("report_id")
    new_status = data.get("new_status")
    user = get_current_user()
    operator = user.get("full_name") if user else data.get("operator", "IMD Duty Officer")
    notes = data.get("notes", "")
    new_cat = data.get("new_category")

    if not report_id or not new_status:
        return jsonify({"error": "report_id and new_status required"}), 400

    ok = moderate_report(report_id, new_status, operator, notes, new_cat)
    if not ok:
        return jsonify({"error": "Report not found"}), 404

    return jsonify({"success": True, "report_id": report_id, "new_status": new_status})

@app.route("/api/admin/audit-logs", methods=["GET"])
@role_required(["admin", "meteorologist"])
def api_audit_logs():
    """Returns moderation audit trail."""
    limit = int(request.args.get("limit", 50))
    logs = get_audit_logs(limit=limit)
    return jsonify(logs)

@app.route("/api/admin/retrain", methods=["POST"])
@role_required(["admin", "meteorologist"])
def api_retrain_feedback():
    """Incorporates analyst corrections into the active ML model."""
    res = feedback_manager.apply_pending_feedback()
    return jsonify(res)

# ==========================================
# Data Export (CSV / JSON)
# ==========================================

@app.route("/api/export/csv", methods=["GET"])
def export_csv():
    """Exports filtered weather reports as CSV."""
    reports = query_reports(limit=1000)
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Report ID", "Source", "Author", "Timestamp", "City", "State",
        "Category", "Confidence", "Is Fake", "Authenticity Score", "Status", "Raw Text"
    ])

    for r in reports:
        writer.writerow([
            r["report_uuid"], r["source_type"], r["author_handle"],
            r["timestamp"], r["city"], r["state"], r["detected_category"],
            r["category_confidence"], r["is_fake"], r["authenticity_score"],
            r["verification_status"], r["raw_text"]
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=imd_weather_big_data_reports.csv"}
    )

@app.route("/api/export/json", methods=["GET"])
def export_json():
    """Exports filtered weather reports as JSON."""
    reports = query_reports(limit=1000)
    return Response(
        json.dumps(reports, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment;filename=imd_weather_big_data_reports.json"}
    )

if __name__ == "__main__":
    print(f"================================================================")
    print(f" National Weather Big Data Analytics Platform (NWBDAP)")
    print(f" Ministry of Earth Sciences | India Meteorological Department")
    print(f" Running at http://localhost:{config.PORT}")
    print(f"================================================================")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
