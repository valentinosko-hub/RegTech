-- RegOps Hub — Lakebase (Postgres) schema.
-- Phase 1 does not run this; it exists so Phase 2 can `psql -f` it against
-- the Lakebase instance referenced by LAKEBASE_CONNECTION_STRING.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SEQUENCE IF NOT EXISTS case_id_seq START 2850;

CREATE TABLE IF NOT EXISTS cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'investigating', 'pending_vendor', 'closed')),
    severity TEXT NOT NULL CHECK (severity IN ('P1', 'P2', 'P3', 'P4')),
    jurisdiction TEXT,
    vendor TEXT,
    case_type TEXT NOT NULL DEFAULT 'incident' CHECK (case_type IN ('incident', 'task', 'query')),
    owner TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('monitoring_alert', 'recon_break', 'paste', 'manual')),
    source_ref TEXT,
    resolution_type TEXT,
    resolution_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_cases_status_owner ON cases (status, owner);
CREATE INDEX IF NOT EXISTS idx_cases_case_id ON cases (case_id);

CREATE TABLE IF NOT EXISTS timeline_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT NOT NULL REFERENCES cases (case_id),
    event_type TEXT NOT NULL CHECK (
        event_type IN ('created', 'status_changed', 'severity_changed', 'comment_added', 'escalated', 'closed', 'linked')
    ),
    actor TEXT NOT NULL,
    description TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_timeline_events_case_id ON timeline_events (case_id, created_at);

CREATE TABLE IF NOT EXISTS comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT NOT NULL REFERENCES cases (case_id),
    author TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_comments_case_id ON comments (case_id);

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('alert_fired', 'case_assigned', 'report_submitted', 'recon_completed')),
    title TEXT NOT NULL,
    body TEXT,
    link TEXT,
    read BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications (user_id, read);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'analyst' CHECK (role IN ('analyst', 'lead', 'admin')),
    shift_start TIME,
    shift_end TIME,
    active BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS vendors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    contacts JSONB,
    feed_cadence_minutes INTEGER,
    active BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS regulatory_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    frequency TEXT NOT NULL CHECK (frequency IN ('daily', 'weekly', 'monthly')),
    deadline_time TIME NOT NULL,
    timezone TEXT NOT NULL DEFAULT 'UTC',
    active BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS regulatory_calendar (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    regulatory_report_id UUID REFERENCES regulatory_reports (id),
    due_date DATE NOT NULL,
    due_time TIMESTAMPTZ NOT NULL,
    assignee TEXT,
    status TEXT NOT NULL DEFAULT 'upcoming' CHECK (status IN ('upcoming', 'due_today', 'completed', 'missed'))
);

CREATE TABLE IF NOT EXISTS mapping_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_pattern TEXT NOT NULL,
    source_pattern TEXT NOT NULL,
    target_pattern TEXT NOT NULL,
    resolution_description TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS briefings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    briefing_date DATE NOT NULL,
    shift TEXT NOT NULL DEFAULT 'morning',
    content TEXT NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Synced caches (populated from Delta via synced tables / periodic refresh)
CREATE TABLE IF NOT EXISTS active_alerts (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    source_vendor TEXT,
    source_report TEXT,
    severity TEXT NOT NULL,
    description TEXT NOT NULL,
    ai_assessment TEXT,
    detected_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_active_alerts_severity ON active_alerts (severity);

CREATE TABLE IF NOT EXISTS today_submissions (
    submission_id TEXT PRIMARY KEY,
    report_name TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    status TEXT NOT NULL,
    due_time TIMESTAMPTZ NOT NULL,
    submitted_at TIMESTAMPTZ,
    sla_met BOOLEAN
);
CREATE INDEX IF NOT EXISTS idx_today_submissions_status ON today_submissions (status);
