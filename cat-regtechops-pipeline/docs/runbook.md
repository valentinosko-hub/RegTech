# CAT Pipeline Operational Runbook

## 1. Deployment Checklist
1. Run `sql/create_tables.sql` in Databricks SQL Warehouse or notebook.
2. Run `sql/create_views.sql`.
3. Import or sync notebooks under `cat-regtechops-pipeline/notebooks/`.
4. Create/update job from `jobs/cat_hourly_job.json`.
5. Verify secret scope contains key `TR-S3-CAT-SSHKey`.
6. Place error dictionary JSON at configured path:
   `abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/reference/cat_error_dictionary_full_v4_1_0.json`

## 2. Scheduling
- Frequency: hourly (`0 0 * * * ?`, UTC)
- Job tasks:
  1. `00_sftp_pull`
  2. `01_parse_files`
  3. `02_enrich_errors`
  4. `03_monitoring`
- Max concurrent runs: 1

## 3. Table Design Reference
All tables are external Delta in schema `regtech_ops_stg`:
- `bi_output_regtechops_cat_file_registry`
- `bi_output_regtechops_cat_meta_feedback`
- `bi_output_regtechops_cat_linkage_errors`
- `bi_output_regtechops_cat_raw_submissions`
- `bi_output_regtechops_cat_error_dictionary`
- `bi_output_regtechops_cat_enriched_errors`
- `bi_output_regtechops_cat_trade_status`
- `bi_output_regtechops_cat_process_log`

All include `created_ts` and `updated_ts`.

## 4. Standard Operating Procedure (Hourly)
1. Confirm latest job run status in Databricks Jobs UI.
2. Check `bi_output_regtechops_cat_process_log` for notebook-level status.
3. Check unknown errors view:
   `regtech_ops_stg.bi_output_regtechops_vw_cat_unknown_error_codes`
4. Check stuck files:
   records with `PROCESSING` for more than 2 hours.

## 5. Failure Recovery
### 5.1 SFTP Failure
- Validate host reachability and key secret.
- Re-run `00_sftp_pull`; idempotency prevents duplicate SUCCESS records.

### 5.2 Parse Failure
- Inspect `error_message` in file registry.
- Validate file landed path and file content.
- Re-run `01_parse_files`; rows merge by deterministic keys.

### 5.3 Enrichment Failure
- Validate dictionary path and JSON validity.
- Re-run `02_enrich_errors`; dictionary load is no-op if already loaded.

### 5.4 Monitoring Failure
- Resolve stuck files or downstream runtime issues.
- Re-run `03_monitoring`.

## 6. Backfill Procedure
1. Copy historical files to SFTP `/cat` or manually register and land them.
2. Execute tasks in order (`00` -> `01` -> `02` -> `03`).
3. Validate reconciliation view by `trade_date`.
