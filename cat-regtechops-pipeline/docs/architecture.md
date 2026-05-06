# CAT RegTechOps Pipeline Architecture

## 1. Architecture Diagram
See Mermaid source: `diagrams/architecture.mmd`

## 2. Components
### 2.1 SFTP Ingestion Layer
- Notebook: `notebooks/00_sftp_pull.py`
- Connects via SFTP (`transfer.s3.com`, key from Databricks secret).
- Detects only new files using deterministic file fingerprint (`file_name + size + modified_ts`).
- Persists raw files to ABFSS landing path by `trade_date/file_fingerprint/file_name`.

### 2.2 Parsing Layer
- Notebook: `notebooks/01_parse_files.py`
- Reads from file registry where `lifecycle_status = SUCCESS` and parse pending.
- Parses by file type with no destructive overwrite.
- Stores immutable raw payload history.

### 2.3 Enrichment & Reconciliation Layer
- Notebook: `notebooks/02_enrich_errors.py`
- Loads CAT dictionary once into `bi_output_regtechops_cat_error_dictionary`.
- Left-joins parsed errors by `error_code`.
- Unknown codes are retained with `UNKNOWN_ERROR_CODE`.
- Builds trade status from submissions minus matched errors.

### 2.4 Monitoring & Operations Layer
- Notebook: `notebooks/03_monitoring.py`
- Generates pipeline health, stuck-processing checks, unknown code counts.
- Logs every notebook execution to process log table.

## 3. Idempotency Strategy
1. **File-level idempotency:** `file_fingerprint` prevents duplicate SUCCESS ingestion.
2. **Row-level idempotency:** deterministic hash IDs for every persisted parsed/enriched row.
3. **No overwrite policy:** all tables append/merge with immutable keys and historical retention.
4. **Late/corrected support:** same filename with changed size/mtime gets a new fingerprint and is processed as a new lifecycle instance.

## 4. Phase 2 Ready Design (Not Implemented)
- Event-type-specific parser registry.
- Event schema catalog and validation hooks.
- Versioned parsing contracts per CAT event type.
