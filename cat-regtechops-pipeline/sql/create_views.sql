-- =============================================================================
-- CAT RegTechOps — analytical views (schema regtech_ops_stg)
-- =============================================================================

USE SCHEMA regtech_ops_stg;

CREATE OR REPLACE VIEW regtech_ops_stg.bi_output_regtechops_cat_vw_accepted_submissions AS
SELECT
  s.raw_submission_id,
  s.file_registry_id,
  r.file_name,
  s.trade_date,
  s.event_type,
  s.raw_record,
  t.created_ts
FROM regtech_ops_stg.bi_output_regtechops_cat_raw_submissions s
JOIN regtech_ops_stg.bi_output_regtechops_cat_file_registry r
  ON s.file_registry_id = r.file_registry_id
JOIN regtech_ops_stg.bi_output_regtechops_cat_trade_status t
  ON s.raw_submission_id = t.raw_submission_id
WHERE t.status = 'ACCEPTED';

CREATE OR REPLACE VIEW regtech_ops_stg.bi_output_regtechops_cat_vw_rejected_submissions AS
SELECT
  s.raw_submission_id,
  s.file_registry_id,
  r.file_name,
  s.trade_date,
  s.event_type,
  s.raw_record,
  t.error_code,
  t.error_description,
  t.updated_ts
FROM regtech_ops_stg.bi_output_regtechops_cat_raw_submissions s
JOIN regtech_ops_stg.bi_output_regtechops_cat_file_registry r
  ON s.file_registry_id = r.file_registry_id
JOIN regtech_ops_stg.bi_output_regtechops_cat_trade_status t
  ON s.raw_submission_id = t.raw_submission_id
WHERE t.status = 'REJECTED';

CREATE OR REPLACE VIEW regtech_ops_stg.bi_output_regtechops_cat_vw_file_health AS
SELECT
  trade_date,
  registry_status,
  file_kind,
  COUNT(*) AS file_cnt,
  MAX(updated_ts) AS last_update_ts
FROM regtech_ops_stg.bi_output_regtechops_cat_file_registry
GROUP BY trade_date, registry_status, file_kind
ORDER BY trade_date DESC, registry_status, file_kind;

CREATE OR REPLACE VIEW regtech_ops_stg.bi_output_regtechops_cat_vw_recent_failures AS
SELECT
  file_registry_id,
  file_name,
  trade_date,
  file_kind,
  registry_status,
  status_detail,
  updated_ts
FROM regtech_ops_stg.bi_output_regtechops_cat_file_registry
WHERE registry_status = 'FAILED'
ORDER BY updated_ts DESC
LIMIT 500;
