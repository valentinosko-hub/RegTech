# Operational runbook

## Prerequisites

1. Run `sql/create_tables.sql` and `sql/create_views.sql` in a Databricks SQL warehouse or notebook **once per environment** (catalog/schema must exist; storage credentials for the `abfss://analysis@stgdpdlwe...` locations must be configured on the cluster / SQL warehouse).
2. Upload `resources/cat_error_dictionary_full_v4_1_0.json` to the DBFS path configured as `error_dictionary_path` (default in job JSON: `dbfs:/FileStore/regtech/cat_error_dictionary_full_v4_1_0.json`).
3. Create secret scope (default `regtech-ops`) with:
   - `TR-S3-CAT-SSHKey` — PEM private key text for SFTP.
   - `CAT_SFTP_USERNAME` — SFTP login, **or** leave absent and set job/widget `sftp_username_fallback`.
4. Import notebooks from `notebooks/*.py` into the Workspace path referenced by `jobs/cat_hourly_job.json` (template uses `/Repos/PROD/cat-regtechops-pipeline/notebooks/...` — adjust to your repo mount).
5. Deploy `jobs/cat_hourly_job.json` via Databricks **Jobs API** or UI (import JSON).

## Hourly execution

- Job concurrency `max_concurrent_runs = 1` prevents overlapping pulls against the same staging directory semantics.
- Staging directory (`staging_dbfs_dir`) must be on **DBFS local disk** (`/dbfs/...`) so Paramiko-written files are visible to executors and drivers consistently for Phase 1.

## Failure modes

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| SFTP auth failure | Wrong username / key format | Validate secrets; test `paramiko` locally with same PEM |
| `FAILED` in registry for parse | Corrupt bz2 or unexpected encoding | Inspect `status_detail`; re-copy file after vendor republish; reset registry row to allow retry |
| Dictionary load error | Missing JSON at `error_dictionary_path` | Upload JSON; rerun `02` |
| Trade status empty | `02` not run after `01` | Ensure job order; run `02` manually |
| Views empty | No `SUCCESS` rows or trade_status not populated | Check `03_monitoring` file health view |

## Retrying a failed file

1. Identify `file_registry_id` from `bi_output_regtechops_cat_file_registry` where `registry_status = 'FAILED'`.
2. Fix root cause (file on vendor side or parser bug).
3. Set `registry_status = 'DISCOVERED'`, clear misleading `status_detail`, ensure `local_staging_path` points to a valid object (re-run `00` if needed).
4. Rerun job from task `01_parse_files` onward.

## Security

- SSH private key never logged; Paramiko loads directly from Databricks secrets.
- `StrictHostKeyChecking` is not disabled in Paramiko transport by default template; add host keys if your security baseline requires known_hosts pinning.

## Observability

- `bi_output_regtechops_cat_process_log` — append-only run records per notebook invocation.
- `03_monitoring` — quick charts for operators (optionally attach to a dashboard job).
