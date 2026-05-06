# CAT RegTechOps Pipeline — Error Handling

## Design Principles

1. **No silent failures.** Every error is logged to `bi_output_regtechops_cat_process_log`
   and the file registry with a full error message.
2. **File-level isolation.** One bad file never blocks processing of other files.
3. **Unknown error codes are non-fatal.** Missing dictionary entries produce `UNKNOWN_ERROR_CODE`
   and the pipeline continues.
4. **Retryable.** All processing is idempotent. Re-running any notebook after a fix is safe.

---

## Error Categories

### 1. SFTP Connectivity Errors

**What:** SSH connection failure, authentication failure, directory listing timeout.

**How handled:**
- `00_sftp_pull` catches all `paramiko` exceptions
- Full stack trace logged to `cat_process_log` with `stage=SFTP_PULL, status=FAILED`
- Job task fails and Databricks retries up to 2 times (60 s interval)
- After retries exhausted, downstream tasks are skipped (Databricks dependency)

**Common causes:**
- SFTP host unreachable (network issue)
- SSH key mismatch (key rotated without updating secret)
- SFTP username changed

**Resolution:** See runbook Scenario 1.

---

### 2. File Download Errors

**What:** Error writing individual file to ABFSS (permissions, quota, network blip).

**How handled:**
- Individual file download wrapped in `try/except`
- Failed file registered with `status=FAILED, error_message=<traceback>`
- Other files in the same run continue downloading
- Failed file is visible in `v_cat_failed_files`

**Recovery:** Set file status back to `DOWNLOADED` and re-run `01_parse_files`.

---

### 3. File Parse Errors

**What:** Malformed CSV, corrupt bz2, unexpected column count.

**How handled:**
- Each file parse wrapped in `try/except` in `01_parse_files`
- File registry updated to `FAILED` with error message
- `cat_process_log` receives `stage=PARSE_FILE, status=FAILED`
- Other files continue parsing

**Safe_get pattern:** All positional CSV access uses `safe_get(lst, idx, default=None)` which
returns `None` for out-of-bounds indices rather than raising `IndexError`. This prevents a
single unexpected column count from failing an entire meta file.

**bz2 decode errors:** Handled with `errors='replace'` — corrupted bytes become `U+FFFD`
(replacement character). The raw record is still stored and visible.

---

### 4. Error Dictionary Miss (UNKNOWN_ERROR_CODE)

**What:** An error file contains an error code that is not in `cat_error_dictionary`.

**How handled:**
- `left join` in `02_enrich_errors` — unmatched codes produce NULL in enrichment columns
- Post-join `coalesce`: `NULL → 'UNKNOWN_ERROR_CODE'` for description, `'UNKNOWN'` for category
- Pipeline continues normally
- Unknown codes visible in `03_monitoring` (section 10) and via:
  ```sql
  SELECT error_code, COUNT(*) AS cnt
  FROM regtech_ops_stg.bi_output_regtechops_cat_enriched_errors
  WHERE error_description = 'UNKNOWN_ERROR_CODE'
  GROUP BY error_code ORDER BY cnt DESC;
  ```

**Resolution:** Update the JSON dictionary, re-upload to ABFSS, re-run `02_enrich_errors`.
The enrichment step processes all rows where `error_description IS NULL`, so previously unknown
codes are enriched as soon as the dictionary is updated.

---

### 5. Duplicate Processing Prevention

**Meta files:** Deduplicated on `(source_file_name, stage)` via `left_anti` join before append.

**Submission files:** Deduplication check: `COUNT(*) WHERE source_file_name = '<file>'` before write.
If count > 0, write is skipped with a log message.

**Error files:** Same source_file_name count check before write.

**Trade status:** MERGE on `(source_file_name, error_roe_id, status='REJECTED')` — only inserts
if the combination doesn't exist.

**File registry:** MERGE on `file_id` — upserts without creating duplicates.

---

### 6. Schema Evolution

`delta.schema.autoMerge.enabled = true` is set at the cluster level. If a new column is
added to a target table in a future code version, the `mergeSchema` option ensures Spark
appends the new column rather than failing the write.

---

## Error Propagation Rules

| Failure type | Impact | Downstream continues? |
|---|---|---|
| SFTP unreachable | No files downloaded this run | No (job retries, then fails) |
| Single file download error | One file stays FAILED | Yes, other files proceed |
| Single file parse error | One file stays FAILED | Yes, other files proceed |
| Dictionary not found | Enrichment step fails | No (raises RuntimeError) |
| Delta MERGE conflict | Notebook fails | No (retry manually) |

---

## Idempotency Matrix

| Operation | Idempotency mechanism |
|---|---|
| SFTP file detection | `file_id` SHA-256 hash checked against registry |
| File download | Registry status prevents re-download of SUCCESS files |
| Meta file write | `left_anti` join on `(source_file_name, stage)` |
| Submission write | Pre-flight count check on `source_file_name` |
| Error file write | Pre-flight count check on `source_file_name` |
| Dictionary bootstrap | `filter(~col("error_code").isin(existing_codes))` |
| Error enrichment | `filter(col("error_description").isNull())` — only processes unenriched rows |
| Trade status | MERGE on natural key |

---

## Logging Schema

Every event logs to `bi_output_regtechops_cat_process_log`:

| Column | Description |
|---|---|
| `log_id` | UUID per log event |
| `run_id` | Job run identifier (format: `run_YYYYMMDD_HHMMSS`) |
| `notebook` | Which notebook generated this entry |
| `stage` | Logical sub-stage (e.g. `SFTP_PULL`, `FILE_DOWNLOAD`, `PARSE_FILE`) |
| `status` | `STARTED`, `SUCCESS`, `FAILED`, `WARN`, `NO_PENDING_FILES`, `NO_NEW_FILES` |
| `message` | Human-readable description (max 4096 chars) |
| `file_name` | File name if applicable |
| `records_in` | Input record count |
| `records_out` | Output record count |
| `duration_ms` | Wall-clock time for this step |

Retention: process log is configured with `delta.logRetentionDuration = 90 days`.
