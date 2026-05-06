# CAT RegTechOps SFTP Ingestion and Reconciliation

## Overview

This project implements the hourly CAT SFTP ingestion and reconciliation pipeline for RegTechOps staging.

Mandatory deployment targets:

| Item | Value |
| --- | --- |
| Schema | `regtech_ops_stg` |
| Table prefix | `bi_output_regtechops_` |
| Storage root | `abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/` |
| SFTP host | `transfer.s3.com` |
| SFTP directory | `/cat` |
| Connection type | `SFTP` |
| SSH key secret | `TR-S3-CAT-SSHKey` |
| Schedule | Hourly |

All Delta tables are external tables with explicit `LOCATION` clauses. No managed tables or default-schema tables are created.

## Business Process

1. CAT files arrive randomly under `/cat`.
2. The pipeline discovers only unseen file versions.
3. Files are landed to ADLS under the RegTechOps external storage root.
4. Meta feedback files are parsed as no-header positional CSV.
5. Submission and delete files are stored as raw records.
6. Ingestion and linkage error files parse only the first three fields and retain the original record as `raw_record`.
7. Error codes are enriched exclusively from the CAT error dictionary Delta table.
8. Trade status is reconciled as:
   - `REJECTED` when the raw submitted record exists in an error file.
   - `ACCEPTED` when no matching error record exists.

## Repository Contents

| Path | Purpose |
| --- | --- |
| `notebooks/00_sftp_pull.py` | Discover and land new SFTP file versions. |
| `notebooks/01_parse_files.py` | Load dictionary and parse landed files. |
| `notebooks/02_enrich_errors.py` | Enrich error rows and build trade status. |
| `notebooks/03_monitoring.py` | Operational summaries and optional quality gates. |
| `sql/create_tables.sql` | External Delta DDL for all required tables. |
| `sql/create_views.sql` | Operational views. |
| `jobs/cat_hourly_job.json` | Databricks hourly job definition. |
| `diagrams/architecture.mmd` | Mermaid architecture diagram. |

## Deployment Notes

Before enabling the job, place the provided CAT error dictionary JSON at:

`abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/_config/cat_error_dictionary_full_v4_1_0.json`

The notebook parameter `error_dictionary_path` can override this path.

## Table Design

| Table | Purpose |
| --- | --- |
| `bi_output_regtechops_cat_file_registry` | Immutable file-version registry and lifecycle status. |
| `bi_output_regtechops_cat_meta_feedback` | Positional CAT acknowledgement, integrity, and ingestion feedback rows. |
| `bi_output_regtechops_cat_linkage_errors` | Raw ingestion/linkage error rows with first three fields parsed and remainder stored as `raw_record`. |
| `bi_output_regtechops_cat_raw_submissions` | Raw submission and delete records without schema enforcement. |
| `bi_output_regtechops_cat_error_dictionary` | Delta copy of the CAT v4.1.0 r15 error dictionary; the only source for error enrichment. |
| `bi_output_regtechops_cat_enriched_errors` | Error rows enriched with description, category, and processing stage from the dictionary. |
| `bi_output_regtechops_cat_trade_status` | Current accepted/rejected status for each raw submitted record. |
| `bi_output_regtechops_cat_process_log` | Batch, file, parser, reconciliation, and monitoring execution history. |
