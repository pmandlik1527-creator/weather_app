-- National Weather Big Data Analytics Platform (NWBDAP)
-- Database Schema for MoES / IMD - Problem Statement 26069

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- Enriched Weather Reports table
CREATE TABLE IF NOT EXISTS weather_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_uuid TEXT UNIQUE NOT NULL,
    source_type TEXT NOT NULL, -- twitter, citizen, open_meteo, instagram, news
    source_url TEXT,
    author_handle TEXT,
    author_credibility_tier TEXT DEFAULT 'social_public',
    source_credibility_score REAL DEFAULT 60.0,
    raw_text TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    city TEXT,
    state TEXT,
    detected_category TEXT NOT NULL,
    category_confidence REAL DEFAULT 0.0,
    is_fake INTEGER DEFAULT 0,
    authenticity_score REAL DEFAULT 85.0,
    fake_reasons TEXT DEFAULT '[]', -- JSON array
    verification_status TEXT DEFAULT 'unverified', -- verified, unverified, flagged_fake, rejected, analyst_overridden
    severity_level TEXT DEFAULT 'moderate', -- mild, moderate, severe, extreme
    cluster_id INTEGER,
    media_urls TEXT DEFAULT '[]', -- JSON array
    citizen_contact TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (cluster_id) REFERENCES incident_clusters(id) ON DELETE SET NULL
);

-- Real-world Incident Clusters (Deduplicated Events)
CREATE TABLE IF NOT EXISTS incident_clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_uuid TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT DEFAULT 'moderate',
    center_lat REAL NOT NULL,
    center_lon REAL NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    report_count INTEGER DEFAULT 1,
    first_reported_at TEXT NOT NULL,
    last_reported_at TEXT NOT NULL,
    status TEXT DEFAULT 'active', -- active, resolved, archived
    summary TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Data Ingestion Source Registry
CREATE TABLE IF NOT EXISTS sources_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    target_query TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    polling_interval_seconds INTEGER DEFAULT 10,
    total_ingested INTEGER DEFAULT 0,
    last_poll_at TEXT,
    health_status TEXT DEFAULT 'healthy'
);

-- Human-in-the-Loop Moderation Audit Logs
CREATE TABLE IF NOT EXISTS moderation_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    operator_name TEXT NOT NULL DEFAULT 'IMD Meteorologist',
    action_type TEXT NOT NULL, -- verify, flag_fake, update_category, reject
    previous_status TEXT,
    new_status TEXT,
    previous_category TEXT,
    new_category TEXT,
    notes TEXT,
    timestamp TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (report_id) REFERENCES weather_reports(id) ON DELETE CASCADE
);

-- Machine Learning Continuous Feedback Log
CREATE TABLE IF NOT EXISTS ml_feedback_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    text_snippet TEXT NOT NULL,
    predicted_category TEXT NOT NULL,
    corrected_category TEXT NOT NULL,
    was_fake_predicted INTEGER NOT NULL,
    was_fake_corrected INTEGER NOT NULL,
    retrained_status INTEGER DEFAULT 0,
    timestamp TEXT DEFAULT (datetime('now'))
);

-- System Performance & Ingestion Telemetry
CREATE TABLE IF NOT EXISTS system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    timestamp TEXT DEFAULT (datetime('now'))
);

-- Indices for rapid dashboard filtering and spatial querying
CREATE INDEX IF NOT EXISTS idx_reports_category ON weather_reports(detected_category);
CREATE INDEX IF NOT EXISTS idx_reports_city ON weather_reports(city);
CREATE INDEX IF NOT EXISTS idx_reports_state ON weather_reports(state);
CREATE INDEX IF NOT EXISTS idx_reports_status ON weather_reports(verification_status);
CREATE INDEX IF NOT EXISTS idx_reports_is_fake ON weather_reports(is_fake);
CREATE INDEX IF NOT EXISTS idx_reports_timestamp ON weather_reports(timestamp);
CREATE INDEX IF NOT EXISTS idx_reports_cluster ON weather_reports(cluster_id);
CREATE INDEX IF NOT EXISTS idx_clusters_status ON incident_clusters(status);

-- User Accounts & Role-Based Access Control
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'citizen', -- 'admin', 'meteorologist', 'citizen'
    designation TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
