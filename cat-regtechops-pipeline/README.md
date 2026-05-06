# CAT RegTechOps Databricks Pipeline

Production Databricks pipeline for CAT (Consolidated Audit Trail) SFTP ingestion, feedback parsing, error enrichment, and accepted/rejected trade reconciliation.

## Scope

This repository area is intentionally standalone. CAT pipeline assets live under:

```text
cat-regtechops-pipeline/
├── README.md
├── notebooks/
├── sql/
├── jobs/
├── docs/
└── diagrams/
```

The pipeline targets:

| Setting | Value |
| --- | --- |
| Schema | `regtech_ops_stg` |
| Table prefix | `bi_output_regtechops_` |
| Storage root | `abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/` |
| SFTP host | `transfer.s3.com` |
| SFTP directory | `/cat` |
| SSH key secret | `TR-S3-CAT-SSHKey` |
| Schedule | Hourly |

All Delta tables are external tables with explicit table-specific `LOCATION` clauses under the storage root.

## Architecture

```text
CAT SFTP /cat
  -> 00_sftp_pull
  -> ADLS landing + cat_file_registry
  -> 01_parse_files
  -> raw submissions, meta feedback, raw errors, error dictionary
  -> 02_enrich_errors
  -> enriched errors + trade status
  -> 03_monitoring
  -> process log and operational summaries
```

The editable Mermaid diagram is in `diagrams/architecture.mmd`.

## Notebooks

| Notebook | Purpose |
| --- | --- |
| `notebooks/00_sftp_pull.py` | Discovers supported files on SFTP, extracts trade date from the filename, registers immutable file versions, downloads new or retryable files, and updates lifecycle status. Failed downloads are retried on a later discovery run. |
| `notebooks/01_parse_files.py` | Loads the CAT error dictionary once, parses no-header meta feedback positionally, stores raw submission/delete records, and parses only the first three error fields while retaining the original record as `raw_record`. CSV-aware helpers extract event type and matching keys without event-schema parsing. |
| `notebooks/02_enrich_errors.py` | Enriches error records from `bi_output_regtechops_cat_error_dictionary` and reconciles accepted/rejected trade status. |
| `notebooks/03_monitoring.py` | Displays file lifecycle, meta feedback, trade status, unknown error code, and failed file summaries. |

## Reconciliation Logic

There is no accepted-records file.

* Submission files are the source of truth for all submitted trades.
* Error files contain rejected trades only.
* Accepted trades are derived as submitted records with no matching error record.

`02_enrich_errors.py` reconciles status by matching:

1. `trade_date`, extracted from the filename; and
2. `record_match_hash`, calculated from a CSV-aware canonical representation of the submitted raw record and the error file `raw_record` remainder after `error_code,action_type,errorROEID`.

`raw_record_hash` remains available for exact lineage. `record_match_hash` is the safer production match key because it is not sensitive to CSV quoting, leading/trailing field whitespace, BOMs, or line-ending differences.

Status output:

| Condition | Status |
| --- | --- |
| Matching error `raw_record` exists | `REJECTED` |
| No matching error `raw_record` exists | `ACCEPTED` |

The output table is `regtech_ops_stg.bi_output_regtechops_cat_trade_status` and includes `trade_date`, `event_type`, `status`, `error_code`, and `error_description`.

## Idempotency

The implementation is safe to rerun:

* `cat_file_registry.file_key` identifies immutable file versions by remote path, name, size, and modified timestamp.
* File lifecycle is tracked as `DISCOVERED -> PROCESSING -> SUCCESS / FAILED`.
* Raw, enriched, and status tables use deterministic keys and Delta `MERGE`.
* Late-arriving error files update previously accepted records to rejected when a matching raw record appears.
* Corrected files are retained as new immutable file versions when remote size or modified timestamp changes.

## SQL and Job Assets

* `sql/create_tables.sql` creates the required external Delta tables in `regtech_ops_stg`.
* `sql/create_views.sql` creates operational views over the CAT Delta tables.
* `jobs/cat_hourly_job.json` runs the notebooks hourly in this order:
  1. `00_sftp_pull`
  2. `01_parse_files`
  3. `02_enrich_errors`
  4. `03_monitoring`

## Documentation

Additional operational documentation is in `docs/`:

* `overview.md`
* `architecture.md`
* `data_flow.md`
* `reconciliation.md`
* `runbook.md`
* `error_handling.md`
