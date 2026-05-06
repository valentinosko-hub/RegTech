-- Operational views for CAT SFTP ingestion and reconciliation.

CREATE OR REPLACE VIEW regtech_ops_stg.bi_output_regtechops_cat_v_file_registry_latest AS
SELECT
  file_key,
  file_name,
  file_type,
  trade_date,
  file_sequence,
  status,
  first_seen_ts,
  last_seen_ts,
  processed_ts,
  file_size,
  landing_path,
  error_message,
  updated_ts
FROM regtech_ops_stg.bi_output_regtechops_cat_file_registry;

CREATE OR REPLACE VIEW regtech_ops_stg.bi_output_regtechops_cat_v_trade_status_summary AS
SELECT
  trade_date,
  event_type,
  status,
  COUNT(*) AS record_count,
  MAX(updated_ts) AS latest_updated_ts
FROM regtech_ops_stg.bi_output_regtechops_cat_trade_status
GROUP BY trade_date, event_type, status;

CREATE OR REPLACE VIEW regtech_ops_stg.bi_output_regtechops_cat_v_error_summary AS
SELECT
  trade_date,
  error_file_type,
  error_code,
  error_description,
  error_category,
  processing_stage,
  event_type,
  record_match_hash,
  COUNT(*) AS error_count,
  MAX(updated_ts) AS latest_updated_ts
FROM regtech_ops_stg.bi_output_regtechops_cat_enriched_errors
GROUP BY
  trade_date,
  error_file_type,
  error_code,
  error_description,
  error_category,
  processing_stage,
  event_type,
  record_match_hash;

CREATE OR REPLACE VIEW regtech_ops_stg.bi_output_regtechops_cat_v_unknown_error_codes AS
SELECT
  error_code,
  trade_date,
  source_file_name,
  COUNT(*) AS occurrence_count,
  MAX(updated_ts) AS latest_updated_ts
FROM regtech_ops_stg.bi_output_regtechops_cat_enriched_errors
WHERE error_description = 'UNKNOWN_ERROR_CODE'
GROUP BY error_code, trade_date, source_file_name;

CREATE OR REPLACE VIEW regtech_ops_stg.bi_output_regtechops_cat_v_meta_feedback_latest AS
SELECT
  trade_date,
  cat_file_name,
  stage,
  status,
  severity,
  error_code,
  error_count,
  total_records_count,
  error_file_name,
  stage_complete_timestamp,
  updated_ts
FROM regtech_ops_stg.bi_output_regtechops_cat_meta_feedback;
