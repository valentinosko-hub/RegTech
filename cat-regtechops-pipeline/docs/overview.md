# CAT RegTechOps Pipeline — Overview

## Purpose

This pipeline ingests, parses, and reconciles **Consolidated Audit Trail (CAT)** submission files
delivered by FINRA/CAT via SFTP. It runs every hour on Databricks, processes all new files since
the last run, enriches error records against the official CAT error dictionary, computes trade-level
acceptance/rejection status, and exposes an operations dashboard for the RegTech team.

---

## Business Context

eToro (IMID: ETOR, submitter: 93007) is required under SEC Rule 613 to submit daily order event
reports to CAT. Files are delivered to CAT's SFTP server (`transfer.s3.com/cat`) and CAT responds
with meta feedback files (`.ack.csv`, `.integrity.csv`, `.ingestion.csv`) confirming receipt and
validation results. Error files (`.ingestion.error.csv.bz2`, `.linkage.error_*.csv.bz2`) list
rejected records that must be corrected and resubmitted.

---

## System Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| SFTP pull | Databricks + paramiko | Pull files from `transfer.s3.com/cat` |
| Landing zone | ABFSS (Azure Data Lake) | Immutable raw file storage |
| File registry | Delta table | Idempotent lifecycle tracking |
| Parsers | PySpark (driver-side) | Type-specific file parsing |
| Error enrichment | PySpark MERGE | Dictionary join |
| Trade status | PySpark MERGE | REJECTED/ACCEPTED classification |
| Monitoring | Databricks display() | Ops dashboard |
| Orchestration | Databricks Jobs | Hourly scheduled multi-task job |

---

## Key Design Principles

1. **Idempotent** — Every notebook is safe to re-run. Already-processed files are skipped.
2. **No data loss** — Files are never deleted from ABFSS. History is fully preserved.
3. **Late arrival friendly** — Files arriving days after their trade date are processed correctly.
4. **Error isolation** — A single bad file never halts processing of other files.
5. **Trade date authority** — The date in the filename is the business date. Upload date is irrelevant.
6. **Single source of truth for errors** — `bi_output_regtechops_cat_error_dictionary` is the only
   place error descriptions live. No hardcoded error strings in application code.

---

## Storage Layout

```
abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/
├── sftp_landing/
│   └── {trade_date}/
│       └── {filename}            ← raw files exactly as received from SFTP
├── config/
│   └── cat_error_dictionary_full_v4_1_0.json   ← upload once at setup
├── bi_output_regtechops_cat_file_registry/
├── bi_output_regtechops_cat_meta_feedback/
├── bi_output_regtechops_cat_raw_submissions/
├── bi_output_regtechops_cat_error_dictionary/
├── bi_output_regtechops_cat_enriched_errors/
├── bi_output_regtechops_cat_linkage_errors/
├── bi_output_regtechops_cat_trade_status/
└── bi_output_regtechops_cat_process_log/
```

---

## Notebooks

| Notebook | Task key | Purpose |
|----------|----------|---------|
| `00_sftp_pull.py` | `sftp_pull` | Detect new files on SFTP, download to ABFSS |
| `01_parse_files.py` | `parse_files` | Parse all DOWNLOADED files by type |
| `02_enrich_errors.py` | `enrich_errors` | Enrich errors + compute trade status |
| `03_monitoring.py` | `monitoring` | Reconciliation dashboard |

---

## Secrets

| Secret scope | Key | Used by |
|---|---|---|
| `regtech-ops` | `TR-S3-CAT-SSHKey` | `00_sftp_pull` — RSA private key for SFTP auth |

---

## Phase 2 (Design Only)

Phase 2 will add event-type-aware schema parsing for submission files:
- A schema registry mapping CAT event types to Spark schemas
- Individual ACCEPTED record rows (currently only summary rows are stored)
- Full ROEID-based reconciliation between submission and error files

Do not implement Phase 2 changes without a separate design review.
