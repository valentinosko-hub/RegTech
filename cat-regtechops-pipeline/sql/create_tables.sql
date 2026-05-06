-- CAT SFTP ingestion and reconciliation external Delta tables.
-- Mandatory environment:
--   schema: regtech_ops_stg
--   table prefix: bi_output_regtechops_
--   storage root: abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/

CREATE SCHEMA IF NOT EXISTS regtech_ops_stg;

CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_file_registry (
  file_key STRING NOT NULL,
  source_system STRING NOT NULL,
  connection_type STRING NOT NULL,
  sftp_host STRING NOT NULL,
  sftp_directory STRING NOT NULL,
  remote_path STRING NOT NULL,
  file_name STRING NOT NULL,
  file_type STRING NOT NULL,
  trade_date DATE,
  file_sequence STRING,
  submitter STRING,
  reporter STRING,
  file_size BIGINT,
  remote_modified_ts TIMESTAMP,
  landing_path STRING,
  content_hash STRING,
  status STRING NOT NULL,
  first_seen_ts TIMESTAMP NOT NULL,
  last_seen_ts TIMESTAMP NOT NULL,
  processing_started_ts TIMESTAMP,
  processed_ts TIMESTAMP,
  attempt_count BIGINT NOT NULL,
  error_message STRING,
  created_ts TIMESTAMP NOT NULL,
  updated_ts TIMESTAMP NOT NULL
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_file_registry'
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_meta_feedback (
  meta_feedback_key STRING NOT NULL,
  source_file_key STRING NOT NULL,
  source_file_name STRING NOT NULL,
  source_file_type STRING NOT NULL,
  trade_date DATE,
  version STRING,
  submitter STRING,
  reporter STRING,
  file_date DATE,
  cat_file_name STRING,
  receipt_timestamp TIMESTAMP,
  stage STRING,
  stage_complete_timestamp TIMESTAMP,
  status STRING,
  severity STRING,
  error_code STRING,
  error_count BIGINT,
  total_records_count BIGINT,
  error_file_name STRING,
  raw_line STRING NOT NULL,
  created_ts TIMESTAMP NOT NULL,
  updated_ts TIMESTAMP NOT NULL
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_meta_feedback'
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_linkage_errors (
  error_record_key STRING NOT NULL,
  source_file_key STRING NOT NULL,
  source_file_name STRING NOT NULL,
  error_file_type STRING NOT NULL,
  trade_date DATE,
  submitter STRING,
  reporter STRING,
  file_sequence STRING,
  row_number BIGINT NOT NULL,
  error_code STRING,
  action_type STRING,
  error_roe_id STRING,
  event_type STRING,
  raw_record STRING,
  record_match_hash STRING,
  raw_line STRING NOT NULL,
  created_ts TIMESTAMP NOT NULL,
  updated_ts TIMESTAMP NOT NULL
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_linkage_errors'
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_raw_submissions (
  submission_record_key STRING NOT NULL,
  source_file_key STRING NOT NULL,
  source_file_name STRING NOT NULL,
  source_file_type STRING NOT NULL,
  trade_date DATE,
  submitter STRING,
  reporter STRING,
  file_sequence STRING,
  row_number BIGINT NOT NULL,
  event_type STRING,
  raw_record STRING NOT NULL,
  raw_record_hash STRING NOT NULL,
  record_match_hash STRING NOT NULL,
  created_ts TIMESTAMP NOT NULL,
  updated_ts TIMESTAMP NOT NULL
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_raw_submissions'
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_error_dictionary (
  error_dictionary_key STRING NOT NULL,
  error_code STRING NOT NULL,
  error_description STRING NOT NULL,
  error_category STRING NOT NULL,
  processing_stage STRING NOT NULL,
  severity STRING,
  source_version STRING,
  source_file STRING,
  created_ts TIMESTAMP NOT NULL,
  updated_ts TIMESTAMP NOT NULL
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_error_dictionary'
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_enriched_errors (
  enriched_error_key STRING NOT NULL,
  error_record_key STRING NOT NULL,
  source_file_key STRING NOT NULL,
  source_file_name STRING NOT NULL,
  error_file_type STRING NOT NULL,
  trade_date DATE,
  submitter STRING,
  reporter STRING,
  file_sequence STRING,
  row_number BIGINT,
  error_code STRING,
  error_description STRING NOT NULL,
  error_category STRING,
  processing_stage STRING,
  action_type STRING,
  error_roe_id STRING,
  event_type STRING,
  raw_record STRING,
  record_match_hash STRING,
  raw_line STRING,
  created_ts TIMESTAMP NOT NULL,
  updated_ts TIMESTAMP NOT NULL
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_enriched_errors'
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_trade_status (
  trade_status_key STRING NOT NULL,
  submission_record_key STRING NOT NULL,
  source_file_key STRING NOT NULL,
  source_file_name STRING NOT NULL,
  trade_date DATE,
  event_type STRING,
  status STRING NOT NULL,
  error_code STRING,
  error_description STRING,
  error_record_key STRING,
  raw_record_hash STRING NOT NULL,
  record_match_hash STRING NOT NULL,
  created_ts TIMESTAMP NOT NULL,
  updated_ts TIMESTAMP NOT NULL
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_trade_status'
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_process_log (
  process_log_id STRING NOT NULL,
  job_run_id STRING,
  task_name STRING NOT NULL,
  file_key STRING,
  source_file_name STRING,
  status STRING NOT NULL,
  started_ts TIMESTAMP NOT NULL,
  completed_ts TIMESTAMP,
  records_read BIGINT,
  records_written BIGINT,
  message STRING,
  exception_class STRING,
  error_message STRING,
  created_ts TIMESTAMP NOT NULL,
  updated_ts TIMESTAMP NOT NULL
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_process_log'
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);
