-- =============================================================================
-- CAT RegTechOps — external Delta DDL (regtech_ops_stg / bi_output_regtechops_*)
-- Storage: abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/<folder>/
-- =============================================================================

USE SCHEMA regtech_ops_stg;

-- -----------------------------------------------------------------------------
-- File registry — SFTP lifecycle and idempotency anchor
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_file_registry (
  file_registry_id            STRING    NOT NULL,
  sftp_remote_path            STRING    NOT NULL,
  file_name                   STRING    NOT NULL,
  trade_date                  DATE      NOT NULL,
  file_kind                   STRING    NOT NULL,
  remote_size_bytes           BIGINT,
  remote_mtime_epoch          BIGINT,
  local_staging_path          STRING,
  file_checksum_sha256        STRING,
  registry_status             STRING    NOT NULL,
  status_detail               STRING,
  last_job_run_id             STRING,
  created_ts                  TIMESTAMP NOT NULL,
  updated_ts                  TIMESTAMP NOT NULL
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/cat_file_registry/'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'comment' = 'CAT SFTP file inventory and processing lifecycle (DISCOVERED/PROCESSING/SUCCESS/FAILED)'
);

-- -----------------------------------------------------------------------------
-- Meta feedback — positional ACK / INTEGRITY / INGESTION rows (no header)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_meta_feedback (
  meta_feedback_id            STRING    NOT NULL,
  file_registry_id            STRING    NOT NULL,
  trade_date                  DATE      NOT NULL,
  meta_subtype                STRING    NOT NULL,
  version                     STRING,
  submitter                   STRING,
  reporter                    STRING,
  file_date                   STRING,
  referenced_file_name        STRING,
  receipt_timestamp           STRING,
  stage                       STRING,
  stage_complete_timestamp    STRING,
  status                      STRING,
  severity                    STRING,
  error_code                  STRING,
  error_count                 STRING,
  total_records_count         STRING,
  raw_meta_line               STRING    NOT NULL,
  created_ts                  TIMESTAMP NOT NULL,
  updated_ts                  TIMESTAMP NOT NULL
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/cat_meta_feedback/'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'comment' = 'CAT meta feedback from *.ack.csv, *.integrity.csv, *.ingestion.csv'
);

-- -----------------------------------------------------------------------------
-- Parsed error-file rows (ingestion + linkage) — pre-dictionary
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_linkage_errors (
  error_row_id                STRING    NOT NULL,
  file_registry_id            STRING    NOT NULL,
  trade_date                  DATE      NOT NULL,
  error_file_type             STRING    NOT NULL,
  error_code                  STRING,
  action_type                 STRING,
  error_roe_id                STRING,
  raw_record                  STRING,
  event_type                  STRING,
  source_line_number          BIGINT,
  created_ts                  TIMESTAMP NOT NULL,
  updated_ts                  TIMESTAMP NOT NULL
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/cat_linkage_errors/'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'comment' = 'Parsed CAT error files: *.ingestion.error.csv.bz2 and *.linkage.error_*.csv.bz2 (first 3 columns + raw_record)'
);

-- -----------------------------------------------------------------------------
-- Raw submissions — *.csv.bz2 submission payloads (no schema enforcement)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_raw_submissions (
  raw_submission_id           STRING    NOT NULL,
  file_registry_id            STRING    NOT NULL,
  trade_date                  DATE      NOT NULL,
  line_number                 BIGINT    NOT NULL,
  raw_record                  STRING    NOT NULL,
  event_type                  STRING,
  created_ts                  TIMESTAMP NOT NULL,
  updated_ts                  TIMESTAMP NOT NULL
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/cat_raw_submissions/'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'comment' = 'CAT submission *.csv.bz2 rows stored as raw text (Phase 1 — no typed schema)'
);

-- -----------------------------------------------------------------------------
-- CAT Appendix E error dictionary (single source of truth for enrichment)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_error_dictionary (
  error_code                  INT       NOT NULL,
  error_description           STRING    NOT NULL,
  error_category              STRING    NOT NULL,
  processing_stage            STRING    NOT NULL,
  source_severity             STRING,
  dictionary_version          STRING    NOT NULL,
  created_ts                  TIMESTAMP NOT NULL,
  updated_ts                  TIMESTAMP NOT NULL
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/cat_error_dictionary/'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'comment' = 'CAT error dictionary v4.1.0 (loaded from JSON — do not hardcode descriptions in notebooks)'
);

-- -----------------------------------------------------------------------------
-- Enriched errors — dictionary join + UNKNOWN_ERROR_CODE fallback
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_enriched_errors (
  enriched_error_id           STRING    NOT NULL,
  error_row_id                STRING    NOT NULL,
  file_registry_id            STRING    NOT NULL,
  trade_date                  DATE      NOT NULL,
  error_file_type             STRING    NOT NULL,
  error_code                  STRING,
  action_type                 STRING,
  error_roe_id                STRING,
  raw_record                  STRING,
  event_type                  STRING,
  error_description           STRING    NOT NULL,
  error_category              STRING    NOT NULL,
  processing_stage            STRING    NOT NULL,
  dictionary_hit              BOOLEAN   NOT NULL,
  created_ts                  TIMESTAMP NOT NULL,
  updated_ts                  TIMESTAMP NOT NULL
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/cat_enriched_errors/'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'comment' = 'Error rows enriched via join to bi_output_regtechops_cat_error_dictionary'
);

-- -----------------------------------------------------------------------------
-- Trade status — submission minus errors (raw-line match, Phase 1)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_trade_status (
  trade_status_id             STRING    NOT NULL,
  raw_submission_id           STRING    NOT NULL,
  file_registry_id            STRING    NOT NULL,
  trade_date                  DATE      NOT NULL,
  event_type                  STRING,
  status                      STRING    NOT NULL,
  error_code                  STRING,
  error_description           STRING,
  created_ts                  TIMESTAMP NOT NULL,
  updated_ts                  TIMESTAMP NOT NULL
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/cat_trade_status/'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'comment' = 'Per submission row: REJECTED if matching error raw_record exists, else ACCEPTED'
);

-- -----------------------------------------------------------------------------
-- Process / job log
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_process_log (
  process_log_id              STRING    NOT NULL,
  notebook_name               STRING    NOT NULL,
  job_run_id                  STRING,
  started_ts                  TIMESTAMP NOT NULL,
  ended_ts                    TIMESTAMP,
  status                      STRING    NOT NULL,
  message                     STRING,
  files_discovered            BIGINT,
  files_processed               BIGINT,
  created_ts                  TIMESTAMP NOT NULL,
  updated_ts                  TIMESTAMP NOT NULL
)
USING DELTA
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/cat_process_log/'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'comment' = 'Operational log for CAT hourly pipeline notebooks'
);
