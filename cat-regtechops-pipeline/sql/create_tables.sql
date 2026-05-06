-- =============================================================================
-- CAT RegTechOps Pipeline — DDL
-- Schema  : regtech_ops_stg
-- Storage : abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/
-- All tables are EXTERNAL Delta tables with explicit LOCATION.
-- Run once at environment setup.  All CREATE statements are idempotent (IF NOT EXISTS).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Schema
-- ---------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS regtech_ops_stg;

-- ---------------------------------------------------------------------------
-- bi_output_regtechops_cat_file_registry
-- Tracks every SFTP file seen by the pipeline and its processing lifecycle.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_file_registry (
    file_id                  STRING        NOT NULL  COMMENT 'SHA-256 of SFTP path (first 32 chars)',
    file_name                STRING        NOT NULL  COMMENT 'Bare filename as it appears on SFTP',
    file_path                STRING        NOT NULL  COMMENT 'Full SFTP path',
    abfss_path               STRING                  COMMENT 'ABFSS path after download',
    file_type                STRING                  COMMENT 'SUBMISSION|ACK|INTEGRITY|INGESTION_META|INGESTION_ERROR|LINKAGE_ERROR|DELETE|UNKNOWN',
    trade_date               DATE                    COMMENT 'Business date extracted from filename',
    submitter                STRING                  COMMENT 'IMID submitter (token 0 of filename)',
    reporter                 STRING                  COMMENT 'CAT reporter (token 1 of filename)',
    file_size_bytes          LONG                    COMMENT 'File size in bytes',
    status                   STRING                  COMMENT 'DISCOVERED|PROCESSING|DOWNLOADED|SUCCESS|FAILED',
    retry_count              INT                     COMMENT 'Number of processing attempts',
    error_message            STRING                  COMMENT 'Last error message if FAILED',
    discovered_ts            TIMESTAMP               COMMENT 'When the file was first seen on SFTP',
    processing_started_ts    TIMESTAMP,
    processing_completed_ts  TIMESTAMP,
    created_ts               TIMESTAMP               NOT NULL,
    updated_ts               TIMESTAMP               NOT NULL
)
USING DELTA
COMMENT 'CAT SFTP file registry — single source of truth for file lifecycle'
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact'   = 'true'
)
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_file_registry/';

-- ---------------------------------------------------------------------------
-- bi_output_regtechops_cat_meta_feedback
-- Parsed content of .ack.csv / .integrity.csv / .ingestion.csv files.
-- One row per meta file (positional CSV, no header).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_meta_feedback (
    meta_id                   STRING    NOT NULL  COMMENT 'Generated UUID',
    source_file_name          STRING              COMMENT 'Source .ack.csv / .ingestion.csv / .integrity.csv filename',
    version                   STRING              COMMENT 'CAT spec version from col[0]',
    submitter                 STRING              COMMENT 'Submitter IMID from col[1]',
    reporter                  STRING              COMMENT 'Reporter IMID from col[2]',
    trade_date                DATE                COMMENT 'Business date from col[3]',
    submission_file_name      STRING              COMMENT 'Corresponding submission file from col[4]',
    receipt_timestamp         TIMESTAMP           COMMENT 'CAT receipt timestamp from col[5]',
    stage                     STRING              COMMENT 'FILE_ACKNOWLEDGEMENT | FILE_INTEGRITY | INGESTION',
    stage_complete_timestamp  TIMESTAMP           COMMENT 'Stage completion timestamp from col[7]',
    status                    STRING              COMMENT 'Success | Failure',
    severity                  STRING              COMMENT 'Error | Warning (when status=Failure)',
    cat_error_code            STRING              COMMENT 'File-level CAT error code from col[10]',
    error_file_name           STRING              COMMENT 'Error file produced by CAT (col[11] when Failure)',
    error_count               LONG                COMMENT 'Number of rejected records (col[12])',
    total_records_count       LONG                COMMENT 'Total submitted records (col[16])',
    raw_line                  STRING              COMMENT 'Full raw CSV line for audit',
    created_ts                TIMESTAMP           NOT NULL,
    updated_ts                TIMESTAMP           NOT NULL
)
USING DELTA
PARTITIONED BY (trade_date)
COMMENT 'Parsed CAT meta feedback files (ack / integrity / ingestion)'
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact'   = 'true'
)
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_meta_feedback/';

-- ---------------------------------------------------------------------------
-- bi_output_regtechops_cat_raw_submissions
-- Raw line-level storage of submission (.csv.bz2) files.
-- No schema enforcement — full event-type parsing deferred to Phase 2.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_raw_submissions (
    submission_id    STRING    NOT NULL  COMMENT 'Generated UUID per line',
    source_file_name STRING              COMMENT 'Source .csv.bz2 filename',
    trade_date       DATE                COMMENT 'Business date from filename',
    submitter        STRING,
    reporter         STRING,
    line_number      LONG                COMMENT '1-based line position in the file',
    raw_record       STRING              COMMENT 'Raw decompressed CSV line. DELETE_MARKER| prefix indicates a DEL record',
    created_ts       TIMESTAMP           NOT NULL,
    updated_ts       TIMESTAMP           NOT NULL
)
USING DELTA
PARTITIONED BY (trade_date)
COMMENT 'Raw CAT submission records — schema-free Phase 1 storage'
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact'   = 'true'
)
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_raw_submissions/';

-- ---------------------------------------------------------------------------
-- bi_output_regtechops_cat_error_dictionary
-- Canonical CAT error code reference loaded from JSON (spec v4.1.0 r15).
-- Single source of truth — do NOT hardcode error descriptions elsewhere.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_error_dictionary (
    error_code        STRING    NOT NULL  COMMENT 'Numeric CAT error code as STRING',
    error_description STRING              COMMENT 'Full description from CAT spec Appendix E',
    error_category    STRING              COMMENT 'Ingestion | Integrity | Linkage | Warning',
    processing_stage  STRING              COMMENT 'Raw stage from JSON: DATA_INGESTION | FILE_INTEGRITY | etc.',
    severity          STRING              COMMENT 'ERROR | WARNING',
    source_version    STRING              COMMENT 'CAT spec version (e.g. 4.1.0 r15)',
    created_ts        TIMESTAMP           NOT NULL,
    updated_ts        TIMESTAMP           NOT NULL
)
USING DELTA
COMMENT 'CAT error code dictionary — source: CAT spec v4.1.0 r15 Appendix E'
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact'   = 'true'
)
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_error_dictionary/';

-- ---------------------------------------------------------------------------
-- bi_output_regtechops_cat_enriched_errors
-- Parsed ingestion error file records with dictionary enrichment.
-- Structure: first 3 cols structured; remainder stored as raw_record.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_enriched_errors (
    error_record_id   STRING    NOT NULL  COMMENT 'Generated UUID',
    source_file_name  STRING              COMMENT 'Source .ingestion.error.csv.bz2 filename',
    file_type         STRING              COMMENT 'Always INGESTION_ERROR in this table',
    trade_date        DATE,
    submitter         STRING,
    reporter          STRING,
    error_code        STRING              COMMENT 'Col[0] from error file',
    action_type       STRING              COMMENT 'Col[1] from error file (NEW|RPR|CANCEL etc.)',
    error_roe_id      STRING              COMMENT 'Col[2]: the errorROEID of the rejected record',
    raw_record        STRING              COMMENT 'Col[3+] joined — the original CAT record',
    event_type        STRING              COMMENT 'raw_record.split(",")[1] — actionType of original record',
    error_description STRING              COMMENT 'From error dictionary (UNKNOWN_ERROR_CODE if not found)',
    error_category    STRING              COMMENT 'Ingestion | Integrity | Linkage | Warning | UNKNOWN',
    processing_stage  STRING,
    created_ts        TIMESTAMP           NOT NULL,
    updated_ts        TIMESTAMP           NOT NULL
)
USING DELTA
PARTITIONED BY (trade_date)
COMMENT 'Parsed and dictionary-enriched ingestion error records'
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact'   = 'true'
)
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_enriched_errors/';

-- ---------------------------------------------------------------------------
-- bi_output_regtechops_cat_linkage_errors
-- Parsed linkage error file records with dictionary enrichment.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_linkage_errors (
    linkage_error_id  STRING    NOT NULL  COMMENT 'Generated UUID',
    source_file_name  STRING              COMMENT 'Source .linkage.error_*.csv.bz2 filename',
    trade_date        DATE,
    submitter         STRING,
    reporter          STRING,
    error_code        STRING,
    action_type       STRING,
    error_roe_id      STRING,
    raw_record        STRING              COMMENT 'Original CAT record (col[3+])',
    event_type        STRING,
    error_description STRING              COMMENT 'From error dictionary (UNKNOWN_ERROR_CODE if not found)',
    error_category    STRING,
    processing_stage  STRING,
    created_ts        TIMESTAMP           NOT NULL,
    updated_ts        TIMESTAMP           NOT NULL
)
USING DELTA
PARTITIONED BY (trade_date)
COMMENT 'Parsed and dictionary-enriched linkage error records'
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact'   = 'true'
)
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_linkage_errors/';

-- ---------------------------------------------------------------------------
-- bi_output_regtechops_cat_trade_status
-- Record-level trade status derived from error files (REJECTED) and meta
-- feedback totals (ACCEPTED summary).  Full record-level ACCEPTED rows
-- require Phase 2 submission parsing.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_trade_status (
    status_id         STRING    NOT NULL  COMMENT 'Generated UUID or error_record_id for REJECTED rows',
    source_file_name  STRING              COMMENT 'Submission file this status refers to',
    trade_date        DATE,
    submitter         STRING,
    reporter          STRING,
    error_roe_id      STRING              COMMENT 'NULL for ACCEPTED summary rows',
    event_type        STRING              COMMENT 'SUMMARY for ACCEPTED summary rows',
    status            STRING              COMMENT 'REJECTED | ACCEPTED',
    error_code        STRING,
    error_description STRING,
    error_category    STRING,
    processing_stage  STRING,
    created_ts        TIMESTAMP           NOT NULL,
    updated_ts        TIMESTAMP           NOT NULL
)
USING DELTA
PARTITIONED BY (trade_date)
COMMENT 'Trade-level acceptance/rejection status per submission file'
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact'   = 'true'
)
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_trade_status/';

-- ---------------------------------------------------------------------------
-- bi_output_regtechops_cat_process_log
-- Operational audit log for every notebook execution step.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS regtech_ops_stg.bi_output_regtechops_cat_process_log (
    log_id       STRING    NOT NULL  COMMENT 'Generated UUID',
    run_id       STRING              COMMENT 'Pipeline run identifier',
    notebook     STRING              COMMENT '00_sftp_pull | 01_parse_files | 02_enrich_errors | 03_monitoring',
    stage        STRING              COMMENT 'Logical processing stage within the notebook',
    status       STRING              COMMENT 'STARTED | SUCCESS | FAILED | WARN | NO_PENDING_FILES | etc.',
    message      STRING,
    file_name    STRING,
    records_in   LONG,
    records_out  LONG,
    duration_ms  LONG,
    created_ts   TIMESTAMP           NOT NULL,
    updated_ts   TIMESTAMP           NOT NULL
)
USING DELTA
COMMENT 'Pipeline execution audit log'
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact'   = 'true',
    'delta.logRetentionDuration'       = 'interval 90 days'
)
LOCATION 'abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/bi_output_regtechops_cat_process_log/';
