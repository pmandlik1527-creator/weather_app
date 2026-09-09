-- ====================================================================
-- National Weather Big Data Analytics Platform (NWBDAP)
-- Supabase / PostgreSQL Schema Definition
-- Ministry of Earth Sciences (MoES) | India Meteorological Department (IMD)
-- Problem Statement ID: 26069
-- ====================================================================
-- Instructions:
-- 1. Open your Supabase Dashboard: https://supabase.com/dashboard
-- 2. Go to "SQL Editor" in the left sidebar.
-- 3. Click "New Query", paste this entire script, and click "Run".
-- ====================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Incident Clusters Table (Deduplicated Real-World Incidents)
CREATE TABLE IF NOT EXISTS incident_clusters (
    id BIGSERIAL PRIMARY KEY,
    cluster_uuid TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT DEFAULT 'moderate',
    center_lat DOUBLE PRECISION NOT NULL,
    center_lon DOUBLE PRECISION NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    report_count INTEGER DEFAULT 1,
    first_reported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_reported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT DEFAULT 'active',
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Enriched Weather Reports Table
CREATE TABLE IF NOT EXISTS weather_reports (
    id BIGSERIAL PRIMARY KEY,
    report_uuid TEXT UNIQUE NOT NULL,
    source_type TEXT NOT NULL,
    source_url TEXT,
    author_handle TEXT,
    author_credibility_tier TEXT DEFAULT 'social_public',
    source_credibility_score NUMERIC DEFAULT 60.0,
    raw_text TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    city TEXT,
    state TEXT,
    detected_category TEXT NOT NULL,
    category_confidence NUMERIC DEFAULT 0.0,
    is_fake SMALLINT DEFAULT 0,
    authenticity_score NUMERIC DEFAULT 85.0,
    fake_reasons JSONB DEFAULT '[]'::jsonb,
    verification_status TEXT DEFAULT 'unverified',
    severity_level TEXT DEFAULT 'moderate',
    cluster_id BIGINT REFERENCES incident_clusters(id) ON DELETE SET NULL,
    media_urls JSONB DEFAULT '[]'::jsonb,
    citizen_contact TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Sources Configuration Table
CREATE TABLE IF NOT EXISTS sources_config (
    id BIGSERIAL PRIMARY KEY,
    source_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    target_query TEXT NOT NULL,
    is_active SMALLINT DEFAULT 1,
    polling_interval_seconds INTEGER DEFAULT 10,
    total_ingested INTEGER DEFAULT 0,
    last_poll_at TIMESTAMPTZ,
    health_status TEXT DEFAULT 'healthy'
);

-- 4. Moderation Audit Logs Table
CREATE TABLE IF NOT EXISTS moderation_audit_logs (
    id BIGSERIAL PRIMARY KEY,
    report_id BIGINT REFERENCES weather_reports(id) ON DELETE CASCADE,
    operator_name TEXT NOT NULL DEFAULT 'IMD Duty Officer',
    action_type TEXT NOT NULL,
    previous_status TEXT,
    new_status TEXT,
    previous_category TEXT,
    new_category TEXT,
    notes TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- 5. ML Feedback Log Table
CREATE TABLE IF NOT EXISTS ml_feedback_log (
    id BIGSERIAL PRIMARY KEY,
    report_id BIGINT,
    text_snippet TEXT NOT NULL,
    predicted_category TEXT NOT NULL,
    corrected_category TEXT NOT NULL,
    was_fake_predicted SMALLINT NOT NULL,
    was_fake_corrected SMALLINT NOT NULL,
    retrained_status SMALLINT DEFAULT 0,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- 6. System Metrics Telemetry Table
CREATE TABLE IF NOT EXISTS system_metrics (
    id BIGSERIAL PRIMARY KEY,
    metric_name TEXT NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_supabase_reports_category ON weather_reports(detected_category);
CREATE INDEX IF NOT EXISTS idx_supabase_reports_city ON weather_reports(city);
CREATE INDEX IF NOT EXISTS idx_supabase_reports_state ON weather_reports(state);
CREATE INDEX IF NOT EXISTS idx_supabase_reports_status ON weather_reports(verification_status);
CREATE INDEX IF NOT EXISTS idx_supabase_reports_is_fake ON weather_reports(is_fake);
CREATE INDEX IF NOT EXISTS idx_supabase_reports_timestamp ON weather_reports(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_supabase_reports_cluster ON weather_reports(cluster_id);
CREATE INDEX IF NOT EXISTS idx_supabase_clusters_status ON incident_clusters(status);

-- Seed Default Sources if not present
INSERT INTO sources_config (source_id, name, source_type, target_query, is_active, polling_interval_seconds)
VALUES 
    ('tw_imd_official', 'Twitter / X #IMD & Weather Tags', 'twitter', '#IMD,#IndiaWeather,#Monsoon,#DelhiRains', 1, 5),
    ('tw_mumbai_rains', 'Twitter / X #MumbaiRains Stream', 'twitter', '#MumbaiRains,#MumbaiFloods', 1, 5),
    ('tw_cyclone_watch', 'Twitter / X Cyclone Alerts', 'twitter', '#CycloneAlert,#BayOfBengal', 1, 10),
    ('citizen_portal', 'Citizen Web & Mobile Reporting Desk', 'citizen', 'direct_submission_api', 1, 1),
    ('open_meteo_imd', 'Open-Meteo Ground Observation Sensors', 'open_meteo', 'national_radar_grid', 1, 30),
    ('ig_weather_photos', 'Instagram Weather Stories & Photos', 'instagram', '#weatherindia,#monsoondairies', 1, 15)
ON CONFLICT (source_id) DO NOTHING;

-- Enable Row Level Security (RLS) with Public Access policies
ALTER TABLE weather_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE incident_clusters ENABLE ROW LEVEL SECURITY;
ALTER TABLE sources_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE moderation_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ml_feedback_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_metrics ENABLE ROW LEVEL SECURITY;

-- Allow anonymous and authenticated read/write access for platform operational API
CREATE POLICY "Allow public read on weather_reports" ON weather_reports FOR SELECT USING (true);
CREATE POLICY "Allow public insert on weather_reports" ON weather_reports FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update on weather_reports" ON weather_reports FOR UPDATE USING (true);

CREATE POLICY "Allow public read on incident_clusters" ON incident_clusters FOR SELECT USING (true);
CREATE POLICY "Allow public insert on incident_clusters" ON incident_clusters FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update on incident_clusters" ON incident_clusters FOR UPDATE USING (true);

CREATE POLICY "Allow public read on sources_config" ON sources_config FOR SELECT USING (true);
CREATE POLICY "Allow public update on sources_config" ON sources_config FOR UPDATE USING (true);

CREATE POLICY "Allow public read on moderation_audit_logs" ON moderation_audit_logs FOR SELECT USING (true);
CREATE POLICY "Allow public insert on moderation_audit_logs" ON moderation_audit_logs FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public read on ml_feedback_log" ON ml_feedback_log FOR SELECT USING (true);
CREATE POLICY "Allow public insert on ml_feedback_log" ON ml_feedback_log FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update on ml_feedback_log" ON ml_feedback_log FOR UPDATE USING (true);

CREATE POLICY "Allow public read on system_metrics" ON system_metrics FOR SELECT USING (true);
CREATE POLICY "Allow public insert on system_metrics" ON system_metrics FOR INSERT WITH CHECK (true);
