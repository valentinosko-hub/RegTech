CREATE VIEW IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_vw_cat_reconciliation_summary AS
SELECT
  trade_date,
  event_type,
  COUNT(*) AS submitted_count,
  SUM(CASE WHEN status = 'REJECTED' THEN 1 ELSE 0 END) AS rejected_count,
  SUM(CASE WHEN status = 'ACCEPTED' THEN 1 ELSE 0 END) AS accepted_count,
  current_timestamp() AS generated_ts
FROM regtech_ops_stg.bi_output_regtechops_cat_trade_status
GROUP BY trade_date, event_type;

CREATE VIEW IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_vw_cat_pipeline_health AS
SELECT
  date_trunc('hour', updated_ts) AS pipeline_hour,
  file_type,
  lifecycle_status,
  parse_status,
  enrich_status,
  COUNT(*) AS file_count,
  MAX(updated_ts) AS last_updated_ts
FROM regtech_ops_stg.bi_output_regtechops_cat_file_registry
GROUP BY
  date_trunc('hour', updated_ts),
  file_type,
  lifecycle_status,
  parse_status,
  enrich_status;

CREATE VIEW IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_vw_cat_unknown_error_codes AS
SELECT
  trade_date,
  source_file_name,
  error_code,
  COUNT(*) AS unknown_error_count,
  MAX(updated_ts) AS last_seen_ts
FROM regtech_ops_stg.bi_output_regtechops_cat_enriched_errors
WHERE error_description = 'UNKNOWN_ERROR_CODE'
GROUP BY trade_date, source_file_name, error_code;
