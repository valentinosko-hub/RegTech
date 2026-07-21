-- RegOps Hub — Delta Lake schema (Unity Catalog: regtech_ops.operational).
-- Phase 1 does not run this; it exists so Phase 3 can execute it against the
-- Databricks SQL warehouse referenced by DATABRICKS_SQL_WAREHOUSE_ID.

CREATE SCHEMA IF NOT EXISTS regtech_ops.operational;

CREATE TABLE IF NOT EXISTS regtech_ops.operational.monitoring_events (
    event_id STRING,
    event_type STRING, -- feed_delay | feed_failure | volume_anomaly | sla_warning | sla_breach | report_status_change
    source_vendor STRING,
    source_report STRING,
    severity STRING, -- info | warning | critical
    description STRING,
    metric_value DOUBLE,
    threshold_value DOUBLE,
    status STRING, -- active | resolved | escalated
    detected_at TIMESTAMP,
    resolved_at TIMESTAMP,
    ai_assessment STRING,
    created_at TIMESTAMP
)
USING DELTA
PARTITIONED BY (DATE(detected_at));

CREATE TABLE IF NOT EXISTS regtech_ops.operational.report_submissions (
    submission_id STRING,
    regulatory_report_id STRING,
    report_name STRING,
    jurisdiction STRING,
    reporting_period DATE,
    status STRING, -- scheduled | generating | validating | queued | submitted | acknowledged | failed | resubmitted
    due_time TIMESTAMP,
    started_at TIMESTAMP,
    submitted_at TIMESTAMP,
    acknowledged_at TIMESTAMP,
    sla_met BOOLEAN,
    record_count INT,
    file_size_bytes LONG,
    error_message STRING,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
USING DELTA
PARTITIONED BY (reporting_period);

CREATE TABLE IF NOT EXISTS regtech_ops.operational.recon_runs (
    run_id STRING,
    recon_set_name STRING,
    jurisdiction STRING,
    run_date DATE,
    source_count INT,
    target_count INT,
    matched_count INT,
    break_count INT,
    match_rate DOUBLE,
    status STRING, -- completed | reviewed | signed_off
    reviewed_by STRING,
    signed_off_at TIMESTAMP,
    created_at TIMESTAMP
)
USING DELTA
PARTITIONED BY (run_date);

CREATE TABLE IF NOT EXISTS regtech_ops.operational.recon_breaks (
    break_id STRING,
    run_id STRING,
    field_name STRING,
    source_value STRING,
    target_value STRING,
    category STRING, -- known_mapping | value_mismatch | date_discrepancy | missing_record | extra_record | novel
    historical_frequency INT,
    ai_explanation STRING,
    status STRING, -- open | resolved | escalated
    resolution_type STRING, -- mapping_applied | resolved_with_note | false_positive | escalated_to_case
    resolution_note STRING,
    resolved_by STRING,
    resolved_at TIMESTAMP,
    linked_case_id STRING,
    linked_mapping_rule_id STRING,
    created_at TIMESTAMP
)
USING DELTA
PARTITIONED BY (DATE(created_at));

CREATE TABLE IF NOT EXISTS regtech_ops.operational.ai_generations (
    generation_id STRING,
    generation_type STRING, -- briefing | alert_assessment | break_explanation | case_extraction
    input_summary STRING,
    output_text STRING,
    confidence DOUBLE,
    model_endpoint STRING,
    prompt_version STRING,
    latency_ms INT,
    token_count INT,
    created_at TIMESTAMP
)
USING DELTA
PARTITIONED BY (DATE(created_at));

-- Call 2 (batch break categorisation), run after daily import:
-- SELECT break_id, ai_classify(
--   CONCAT(field_name, ': ', source_value, ' vs ', target_value),
--   ARRAY('known_mapping', 'value_mismatch', 'date_discrepancy', 'missing_record', 'novel')
-- ) AS category
-- FROM regtech_ops.operational.recon_breaks
-- WHERE run_date = current_date() AND category IS NULL
