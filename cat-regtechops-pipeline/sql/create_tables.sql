CREATE SCHEMA IF NOT EXISTS regtech_ops_stg;

CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_file_registry (
  file_registry_id STRING,
  file_fingerprint STRING,
  file_name STRING,
  remote_path STRING,
  file_type STRING,
  trade_date DATE,
  trade_date_str STRING,
  discovered_ts TIMESTAMP,
  remote_modified_ts TIMESTAMP,
  file_size_bytes BIGINT,
  checksum_sha256 STRING,
  landing_path STRING,
  lifecycle_status STRING,
  parse_status STRING,
  enrich_status STRING,
  retry_count INT,
  source_connection STRING,
  error_message STRING,
  created_ts TIMESTAMP,
  updated_ts TIMESTAMP
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_file_registry/';

CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_meta_feedback (
  feedback_id STRING,
  file_registry_id STRING,
  source_file_name STRING,
  source_file_type STRING,
  trade_date DATE,
  version STRING,
  submitter STRING,
  reporter STRING,
  file_date STRING,
  receipt_timestamp STRING,
  stage STRING,
  stage_complete_timestamp STRING,
  status STRING,
  severity STRING,
  error_code STRING,
  error_count INT,
  total_records_count BIGINT,
  raw_line STRING,
  ingest_ts TIMESTAMP,
  created_ts TIMESTAMP,
  updated_ts TIMESTAMP
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_meta_feedback/';

CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_linkage_errors (
  error_row_id STRING,
  file_registry_id STRING,
  source_file_name STRING,
  source_error_file_type STRING,
  trade_date DATE,
  error_code STRING,
  action_type STRING,
  error_roe_id STRING,
  raw_record STRING,
  raw_record_hash STRING,
  event_type STRING,
  ingest_ts TIMESTAMP,
  created_ts TIMESTAMP,
  updated_ts TIMESTAMP
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_linkage_errors/';

CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_raw_submissions (
  submission_row_id STRING,
  file_registry_id STRING,
  source_file_name STRING,
  source_file_type STRING,
  trade_date DATE,
  raw_record STRING,
  raw_record_hash STRING,
  event_type STRING,
  ingest_ts TIMESTAMP,
  created_ts TIMESTAMP,
  updated_ts TIMESTAMP
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_raw_submissions/';

CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_error_dictionary (
  error_code STRING,
  error_description STRING,
  error_category STRING,
  processing_stage STRING,
  source_version STRING,
  source_file STRING,
  created_ts TIMESTAMP,
  updated_ts TIMESTAMP
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_error_dictionary/';

CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_enriched_errors (
  enriched_error_id STRING,
  error_row_id STRING,
  file_registry_id STRING,
  source_file_name STRING,
  trade_date DATE,
  event_type STRING,
  error_code STRING,
  action_type STRING,
  error_roe_id STRING,
  raw_record STRING,
  raw_record_hash STRING,
  error_description STRING,
  error_category STRING,
  processing_stage STRING,
  created_ts TIMESTAMP,
  updated_ts TIMESTAMP
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_enriched_errors/';

CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_trade_status (
  trade_status_id STRING,
  submission_row_id STRING,
  file_registry_id STRING,
  source_file_name STRING,
  trade_date DATE,
  event_type STRING,
  raw_record_hash STRING,
  status STRING,
  error_code STRING,
  error_description STRING,
  created_ts TIMESTAMP,
  updated_ts TIMESTAMP
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_trade_status/';

CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_process_log (
  process_log_id STRING,
  process_name STRING,
  run_id STRING,
  batch_ts TIMESTAMP,
  status STRING,
  records_read BIGINT,
  records_written BIGINT,
  details STRING,
  error_message STRING,
  created_ts TIMESTAMP,
  updated_ts TIMESTAMP
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_process_log/';
