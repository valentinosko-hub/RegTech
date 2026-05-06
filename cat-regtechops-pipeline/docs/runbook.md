# CAT RegTechOps Pipeline — Operational Runbook

## Scope

This runbook covers routine operations, monitoring, and incident response for the
CAT RegTechOps SFTP pipeline running on Databricks.

---

## Routine Checks

### Verify the hourly job ran

```sql
-- Last 5 pipeline runs
SELECT run_id, MIN(created_ts) AS started, MAX(updated_ts) AS ended,
       MAX(CASE WHEN status='FAILED' THEN 1 ELSE 0 END) AS had_failure
FROM regtech_ops_stg.bi_output_regtechops_cat_process_log
GROUP BY run_id
ORDER BY started DESC
LIMIT 5;
```

Or via Databricks Jobs UI → `CAT_RegTechOps_Hourly_Pipeline` → Runs.

### Check today's reconciliation

```sql
SELECT * FROM regtech_ops_stg.v_cat_daily_reconciliation
WHERE trade_date >= CURRENT_DATE() - INTERVAL 3 DAYS
ORDER BY trade_date DESC;
```

### Check for failed files

```sql
SELECT * FROM regtech_ops_stg.v_cat_failed_files;
```

---

## Incident Response

### Scenario 1: Job failed / no files processed

**Symptoms:** `cat_process_log` shows FAILED status; no new rows in registry.

**Steps:**
1. Check Databricks Jobs UI for the failing task and error message
2. If `sftp_pull` task failed:
   - Verify SFTP connectivity: `ping transfer.s3.com`
   - Verify secret is valid: open `00_sftp_pull` notebook, run the SFTP connect cell interactively
   - Check secret scope `regtech-ops` has key `TR-S3-CAT-SSHKey`
3. Re-run the job manually from the Databricks Jobs UI (idempotent — safe to re-run)

### Scenario 2: Files in FAILED state after download

**Symptoms:** `v_cat_failed_files` shows files with `status = 'FAILED'`

**Steps:**
1. Read `error_message` from the registry row
2. Common causes:
   - ABFSS permission error → verify service principal has `Storage Blob Data Contributor`
   - Corrupt bz2 file → file is stored as-is on ABFSS; check raw bytes
   - Parsing error → examine `cat_process_log` for the file_name
3. To retry a single file: update registry status back to `DOWNLOADED`:
   ```sql
   UPDATE regtech_ops_stg.bi_output_regtechops_cat_file_registry
   SET status = 'DOWNLOADED', error_message = NULL, retry_count = retry_count + 1,
       updated_ts = CURRENT_TIMESTAMP()
   WHERE file_name = '<filename>';
   ```
4. Run `01_parse_files` notebook manually or wait for next hourly run

### Scenario 3: Error records not enriched (`error_description IS NULL`)

**Symptoms:** Monitoring notebook shows unenriched rows; `v_cat_top_errors` shows nulls.

**Steps:**
1. Check dictionary was bootstrapped:
   ```sql
   SELECT COUNT(*) FROM regtech_ops_stg.bi_output_regtechops_cat_error_dictionary;
   -- Expected: 367 rows
   ```
2. If empty: verify `cat_error_dictionary_full_v4_1_0.json` is uploaded to ABFSS:
   ```
   abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/config/cat_error_dictionary_full_v4_1_0.json
   ```
3. Run `02_enrich_errors` notebook manually — it will bootstrap and enrich in one pass

### Scenario 4: New error code not in dictionary

**Symptoms:** `error_description = 'UNKNOWN_ERROR_CODE'` for rows with a specific code.

**Behavior:** Pipeline continues normally; UNKNOWN codes are flagged but not fatal.

**Steps:**
1. Note the unknown code(s) from:
   ```sql
   SELECT error_code, COUNT(*) AS cnt
   FROM regtech_ops_stg.bi_output_regtechops_cat_enriched_errors
   WHERE error_description = 'UNKNOWN_ERROR_CODE'
   GROUP BY error_code;
   ```
2. Check CAT specification for the code (new spec version may have added codes)
3. Update `cat_error_dictionary_full_v4_1_0.json` with the new entry
4. Re-upload to ABFSS config path
5. Run `02_enrich_errors` — the bootstrap step will insert the new code
6. Enrichment of existing UNKNOWN rows will happen automatically (they have `error_description IS NULL`
   which triggers re-enrichment on every run)

### Scenario 5: Duplicate records after re-run

**Behavior by design:** The pipeline is idempotent. If you see apparent duplicates:
1. Check `cat_file_registry` — a file should have exactly one row (keyed by `file_id`)
2. Check `cat_meta_feedback` — deduplicated on `(source_file_name, stage)` during write
3. Check `cat_raw_submissions` — deduplicated on `source_file_name` during write
4. Check `cat_enriched_errors` — deduplicated on `source_file_name` during write
5. Check `cat_trade_status` — idempotent MERGE on `(source_file_name, error_roe_id, status='REJECTED')`

If duplicates exist, they indicate a bug in deduplication logic — open an incident.

### Scenario 6: SFTP file seen on server but not in registry

**Steps:**
1. Verify the file has a recognisable pattern. Files with `file_type = 'UNKNOWN'` are still
   registered but not parsed.
2. If the pattern is new (new event type group, etc.), add a new entry to `FILE_TYPE_PATTERNS`
   in `00_sftp_pull.py` and `01_parse_files.py`.
3. Rerun the pipeline.

---

## Manual Operations

### Re-process a specific trade date

```python
# In a notebook cell — mark all files for a trade_date as DOWNLOADED
spark.sql("""
    UPDATE regtech_ops_stg.bi_output_regtechops_cat_file_registry
    SET status = 'DOWNLOADED', updated_ts = CURRENT_TIMESTAMP()
    WHERE trade_date = '2026-04-27'
      AND status = 'SUCCESS'
      AND abfss_path IS NOT NULL
""")
# Then run 01_parse_files and 02_enrich_errors notebooks
```

**Warning:** This will re-parse files. Deduplication logic prevents duplicate rows in most tables,
but review carefully before executing on production data.

### Check SFTP connectivity manually

```python
# Run in a Databricks notebook cell
import paramiko, io
ssh_key = dbutils.secrets.get("regtech-ops", "TR-S3-CAT-SSHKey")
pkey = paramiko.RSAKey.from_private_key(io.StringIO(ssh_key))
t = paramiko.Transport(("transfer.s3.com", 22))
t.connect(username="93007", pkey=pkey)
sftp = paramiko.SFTPClient.from_transport(t)
files = sftp.listdir("/cat")
print(f"Files on SFTP: {len(files)}")
t.close()
```

### Trigger an immediate pipeline run

From Databricks Jobs UI:
1. Navigate to `CAT_RegTechOps_Hourly_Pipeline`
2. Click **Run now**
3. Optionally pass `run_id = manual_<timestamp>` as a parameter to distinguish the run in logs

---

## Secret Rotation

When `TR-S3-CAT-SSHKey` is rotated:
1. Generate a new RSA key pair
2. Provide the public key to CAT (FINRA/CAT SFTP onboarding contact)
3. Update the Databricks secret:
   ```bash
   databricks secrets put-secret regtech-ops TR-S3-CAT-SSHKey --string-value "$(cat new_id_rsa)"
   ```
4. Test connectivity (see above)
5. No code changes required

---

## Storage Maintenance

### Optimise Delta tables (monthly)

```sql
OPTIMIZE regtech_ops_stg.bi_output_regtechops_cat_file_registry;
OPTIMIZE regtech_ops_stg.bi_output_regtechops_cat_meta_feedback;
OPTIMIZE regtech_ops_stg.bi_output_regtechops_cat_enriched_errors ZORDER BY (trade_date, error_code);
OPTIMIZE regtech_ops_stg.bi_output_regtechops_cat_trade_status ZORDER BY (trade_date);
```

### Vacuum old Delta versions (after 30 days)

```sql
VACUUM regtech_ops_stg.bi_output_regtechops_cat_file_registry RETAIN 720 HOURS;
VACUUM regtech_ops_stg.bi_output_regtechops_cat_raw_submissions RETAIN 720 HOURS;
```

---

## Alerting

Configure Databricks job failure alerts:
1. In job settings → Notifications → On failure → add team email
2. Optional: configure webhook to PagerDuty or Slack

Key thresholds to alert on (Databricks SQL alerts):
- `error_rate_pct > 5` for any trade date → unusual rejection rate
- `v_cat_failed_files` count > 0 for > 2 hours → stuck files
- `v_cat_late_arriving_files` count > 10 → SFTP delivery delay

---

## Environment Setup (one-time)

1. Install `paramiko` as a cluster library on the job cluster
2. Create Databricks secret scope `regtech-ops`
3. Add secret `TR-S3-CAT-SSHKey` with the RSA private key
4. Upload `cat_error_dictionary_full_v4_1_0.json` to:
   `abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/config/`
5. Run `sql/create_tables.sql` once via Databricks SQL editor or notebook
6. Run `sql/create_views.sql` once
7. Import job definition from `jobs/cat_hourly_job.json` via Databricks CLI:
   ```bash
   databricks jobs create --json @jobs/cat_hourly_job.json
   ```
8. Update `notebook_path` values in the job JSON to match your workspace Repos path
