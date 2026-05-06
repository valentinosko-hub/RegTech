# CAT RegTechOps Pipeline — Overview

## Purpose

Hourly ingestion of Consolidated Audit Trail (CAT) artefacts from the industry SFTP endpoint into **external Delta** tables under `regtech_ops_stg`, with **idempotent** file handling, **dictionary-driven** error enrichment, and **submission-minus-errors** trade status for reconciliation.

## Scope (Phase 1)

- SFTP discovery and download (`transfer.s3.com`, directory `/cat`, SSH key secret `TR-S3-CAT-SSHKey`).
- Parse **submissions** (`*.csv.bz2`), **meta** (`*.ack.csv`, `*.integrity.csv`, `*.ingestion.csv`), **errors** (`*.ingestion.error.csv.bz2`, `*.linkage.error_*.csv.bz2`), and **deletes** (`*.DEL.csv.bz2`) without enforcing a typed submission schema.
- Load the CAT Appendix E dictionary JSON once into `bi_output_regtechops_cat_error_dictionary` and join all error rows through that table only (no hardcoded descriptions in notebooks).
- Materialize `bi_output_regtechops_cat_trade_status` as **ACCEPTED** unless a matching **rejected** error row exists (Phase 1 match: trimmed full `raw_record` equality between submission line and error remainder).

## Non-goals (Phase 2 — design only)

- Event-type-aware typed parsing and a per–event-type schema registry.
- Any change to the Phase 1 raw storage model beyond additive columns agreed in a future change request.

## Repository layout

| Path | Role |
|------|------|
| `notebooks/00_sftp_pull.py` | SFTP list, registry insert, download |
| `notebooks/01_parse_files.py` | Parse into fact tables + registry lifecycle |
| `notebooks/02_enrich_errors.py` | Dictionary load, enrichment, trade status |
| `notebooks/03_monitoring.py` | Operational dashboards (SQL) |
| `sql/create_tables.sql` | External Delta DDL with mandatory `LOCATION` |
| `sql/create_views.sql` | Accepted / rejected / health views |
| `jobs/cat_hourly_job.json` | Hourly multi-task job definition |
| `resources/` | Bundled `cat_error_dictionary_full_v4_1_0.json` and sample meta CSVs |
| `diagrams/architecture.mmd` | Mermaid architecture |

## Environment rules (mandatory)

- **Catalog/schema**: use widgets `catalog` / `schema` (default `hive_metastore` / `regtech_ops_stg` or your Unity Catalog target).
- **Table prefix**: `bi_output_regtechops_`.
- **Storage**: every table is **EXTERNAL Delta** under  
  `abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/<table-folder>/`.

## Business dates

- **Trade date** is parsed from the filename token `YYYYMMDD` (example: `93007_ETOR_20260427_Group1_OrderEvents_000001.csv.bz2` → `2026-04-27`). Upload timestamps are stored only as operational metadata, not as business trade date.

## Scheduling

- Databricks job `CAT_RegTechOps_Hourly` (`jobs/cat_hourly_job.json`): sequential tasks `00` → `01` → `02` → `03`, cron **every hour** (UTC in template; adjust `timezone_id` per operations).

## Related documents

- `architecture.md` — components and idempotency.
- `data_flow.md` — file types and landing tables.
- `reconciliation.md` — accepted vs rejected logic.
- `runbook.md` — secrets, paths, and failure recovery.
- `error_handling.md` — meta vs error files and unknown codes.
