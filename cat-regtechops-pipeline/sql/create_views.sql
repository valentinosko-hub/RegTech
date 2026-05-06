-- =============================================================================
-- CAT RegTechOps Pipeline — Views
-- Schema  : regtech_ops_stg
-- Run after create_tables.sql has been executed and tables are populated.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- v_cat_daily_reconciliation
-- One row per trade_date / submitter / reporter showing submission totals,
-- error counts, and derived accepted counts.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW regtech_ops_stg.v_cat_daily_reconciliation AS
SELECT
    m.trade_date,
    m.submitter,
    m.reporter,
    SUM(m.total_records_count)                                        AS total_submitted,
    SUM(m.error_count)                                                AS total_errors,
    SUM(m.total_records_count) - COALESCE(SUM(m.error_count), 0)     AS total_accepted,
    ROUND(
        COALESCE(SUM(m.error_count), 0) /
        NULLIF(SUM(m.total_records_count), 0) * 100, 4
    )                                                                  AS error_rate_pct,
    COUNT(DISTINCT m.submission_file_name)                             AS submission_file_count,
    MIN(m.receipt_timestamp)                                           AS earliest_receipt,
    MAX(m.stage_complete_timestamp)                                    AS latest_completion,
    CURRENT_TIMESTAMP()                                                AS view_ts
FROM regtech_ops_stg.bi_output_regtechops_cat_meta_feedback m
WHERE m.stage = 'INGESTION'
GROUP BY m.trade_date, m.submitter, m.reporter;


-- ---------------------------------------------------------------------------
-- v_cat_file_pipeline_status
-- Full lifecycle view: registry status joined with meta feedback stage results.
-- One row per submission file with a column per stage.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW regtech_ops_stg.v_cat_file_pipeline_status AS
SELECT
    r.file_name                                 AS submission_file,
    r.trade_date,
    r.submitter,
    r.reporter,
    r.file_size_bytes,
    r.status                                    AS registry_status,
    r.discovered_ts,
    r.processing_completed_ts,
    -- ACK
    ack.status                                  AS ack_status,
    ack.stage_complete_timestamp                AS ack_ts,
    -- INTEGRITY
    intg.status                                 AS integrity_status,
    intg.stage_complete_timestamp               AS integrity_ts,
    -- INGESTION
    ing.status                                  AS ingestion_status,
    ing.stage_complete_timestamp                AS ingestion_ts,
    ing.total_records_count,
    ing.error_count,
    ing.total_records_count
        - COALESCE(ing.error_count, 0)          AS accepted_count,
    ing.error_file_name
FROM regtech_ops_stg.bi_output_regtechops_cat_file_registry r
LEFT JOIN regtech_ops_stg.bi_output_regtechops_cat_meta_feedback ack
    ON  ack.submission_file_name = r.file_name
    AND ack.stage = 'FILE_ACKNOWLEDGEMENT'
LEFT JOIN regtech_ops_stg.bi_output_regtechops_cat_meta_feedback intg
    ON  intg.submission_file_name = r.file_name
    AND intg.stage = 'FILE_INTEGRITY'
LEFT JOIN regtech_ops_stg.bi_output_regtechops_cat_meta_feedback ing
    ON  ing.submission_file_name = r.file_name
    AND ing.stage = 'INGESTION'
WHERE r.file_type = 'SUBMISSION';


-- ---------------------------------------------------------------------------
-- v_cat_top_errors
-- Ranked error codes across all error files, enriched with dictionary.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW regtech_ops_stg.v_cat_top_errors AS
SELECT
    trade_date,
    error_code,
    error_description,
    error_category,
    processing_stage,
    'INGESTION' AS error_source,
    COUNT(*)    AS occurrence_count
FROM regtech_ops_stg.bi_output_regtechops_cat_enriched_errors
GROUP BY trade_date, error_code, error_description, error_category, processing_stage

UNION ALL

SELECT
    trade_date,
    error_code,
    error_description,
    error_category,
    processing_stage,
    'LINKAGE' AS error_source,
    COUNT(*)   AS occurrence_count
FROM regtech_ops_stg.bi_output_regtechops_cat_linkage_errors
GROUP BY trade_date, error_code, error_description, error_category, processing_stage;


-- ---------------------------------------------------------------------------
-- v_cat_trade_status_summary
-- Aggregate ACCEPTED / REJECTED totals per trade date and submitter.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW regtech_ops_stg.v_cat_trade_status_summary AS
SELECT
    trade_date,
    submitter,
    reporter,
    status,
    COUNT(*) AS record_count
FROM regtech_ops_stg.bi_output_regtechops_cat_trade_status
GROUP BY trade_date, submitter, reporter, status;


-- ---------------------------------------------------------------------------
-- v_cat_failed_files
-- All files currently in FAILED state with error details.
-- Used by the runbook for remediation.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW regtech_ops_stg.v_cat_failed_files AS
SELECT
    file_id,
    file_name,
    file_type,
    trade_date,
    submitter,
    status,
    retry_count,
    error_message,
    discovered_ts,
    processing_completed_ts,
    DATEDIFF(CURRENT_DATE(), trade_date) AS days_since_trade_date
FROM regtech_ops_stg.bi_output_regtechops_cat_file_registry
WHERE status = 'FAILED'
ORDER BY discovered_ts DESC;


-- ---------------------------------------------------------------------------
-- v_cat_late_arriving_files
-- Files discovered more than 3 calendar days after their trade date.
-- Assists regulatory reporting timeliness monitoring.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW regtech_ops_stg.v_cat_late_arriving_files AS
SELECT
    file_name,
    file_type,
    trade_date,
    discovered_ts,
    DATE_ADD(trade_date, 3)                                   AS expected_latest_date,
    DATEDIFF(CAST(discovered_ts AS DATE), trade_date)         AS days_late,
    status
FROM regtech_ops_stg.bi_output_regtechops_cat_file_registry
WHERE trade_date IS NOT NULL
  AND CAST(discovered_ts AS DATE) > DATE_ADD(trade_date, 3)
ORDER BY days_late DESC;


-- ---------------------------------------------------------------------------
-- v_cat_pipeline_run_summary
-- Latest status per run_id for operational dashboards.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW regtech_ops_stg.v_cat_pipeline_run_summary AS
SELECT
    run_id,
    MIN(created_ts)                               AS run_start,
    MAX(updated_ts)                               AS run_end,
    SUM(records_in)                               AS total_files_in,
    SUM(records_out)                              AS total_files_out,
    MAX(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) AS had_failures,
    COUNT(CASE WHEN status = 'FAILED' THEN 1 END)      AS failure_count,
    SUM(duration_ms)                              AS total_duration_ms
FROM regtech_ops_stg.bi_output_regtechops_cat_process_log
GROUP BY run_id
ORDER BY run_start DESC;
