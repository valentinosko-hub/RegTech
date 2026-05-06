# CAT SFTP Ingestion Runbook

## Hourly operation

Job: `cat-regtechops-hourly-sftp-ingestion-reconciliation`

Task order:

1. `00_sftp_pull`
2. `01_parse_files`
3. `02_enrich_errors`
4. `03_monitoring`

The schedule is hourly (`0 0 * * * ?`) with `max_concurrent_runs = 1`.

## Prerequisites

* Databricks secret scope contains key `TR-S3-CAT-SSHKey`.
* SFTP host `transfer.s3.com` is reachable from the Databricks cluster.
* The CAT error dictionary JSON is available at:
  `abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/_config/cat_error_dictionary_full_v4_1_0.json`.
* SQL in `sql/create_tables.sql` has been executed, or the notebooks have created the required tables on first run.

## Standard checks

```sql
SELECT file_type, status, COUNT(*)
FROM regtech_ops_stg.bi_output_regtechops_cat_file_registry
GROUP BY file_type, status;

SELECT trade_date, event_type, status, COUNT(*)
FROM regtech_ops_stg.bi_output_regtechops_cat_trade_status
GROUP BY trade_date, event_type, status;

SELECT *
FROM regtech_ops_stg.bi_output_regtechops_cat_v_unknown_error_codes
ORDER BY latest_updated_ts DESC;
```

## Reprocessing

The pipeline is idempotent. To retry a failed SFTP pull, set the relevant `file_registry.status` to `DISCOVERED` after resolving the root cause. Parsed files are protected by process-log success entries and target-table merge keys.

## Late files

No manual action is required. A late-arriving error file is registered as a new file version, parsed, enriched, and then causes `cat_trade_status` to update matching submitted raw records from `ACCEPTED` to `REJECTED`.

## Corrected files

Corrected files with the same name but different size or modified time receive a new `file_key`. Prior records remain in Delta history; new records are parsed under the corrected file version.

