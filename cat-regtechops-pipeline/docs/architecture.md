# CAT RegTechOps Pipeline — Architecture

## Mermaid Diagram

See [`diagrams/architecture.mmd`](../diagrams/architecture.mmd) for the full Mermaid source.

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        Databricks Hourly Job                             │
│                                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │00_sftp_pull │→ │01_parse_files│→ │02_enrich_    │→ │03_monitoring│  │
│  │             │  │              │  │  errors       │  │             │  │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘  └─────────────┘  │
│         │                │                  │                            │
└─────────┼────────────────┼──────────────────┼────────────────────────── ┘
          │                │                  │
          ▼                │                  │
   ┌─────────────┐         │                  │
   │ SFTP Server │         │                  │
   │ transfer.s3 │         │                  │
   │ .com/cat    │         │                  │
   └─────────────┘         │                  │
          │                │                  │
          ▼                ▼                  ▼
   ┌───────────────────────────────────────────────────────────────────┐
   │                   Azure Data Lake (ABFSS)                          │
   │                                                                     │
   │  sftp_landing/{trade_date}/{file}  ← raw bytes, immutable          │
   │                                                                     │
   │  Delta Tables (schema: regtech_ops_stg):                            │
   │  ├── cat_file_registry          ← lifecycle of every file          │
   │  ├── cat_meta_feedback          ← ACK/integrity/ingestion feedback  │
   │  ├── cat_raw_submissions        ← raw lines from .csv.bz2 files    │
   │  ├── cat_error_dictionary       ← 367 codes, CAT spec v4.1.0 r15   │
   │  ├── cat_enriched_errors        ← ingestion errors + dict join      │
   │  ├── cat_linkage_errors         ← linkage errors + dict join        │
   │  ├── cat_trade_status           ← REJECTED/ACCEPTED per record     │
   │  └── cat_process_log            ← execution audit log               │
   └───────────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 00_sftp_pull — SFTP Ingestion Layer

- Authenticates via RSA private key from Databricks secrets (`TR-S3-CAT-SSHKey`, scope `regtech-ops`)
- Uses `paramiko` for SFTP (pure Python, no native deps required)
- Lists all files in `/cat` via `sftp.listdir_attr()`
- Computes `file_id` = SHA-256 of SFTP path (32-char prefix) — deterministic across runs
- Checks `cat_file_registry` and skips all already-registered `file_id` values
- Bulk-registers new files as `DISCOVERED`, then transitions through `PROCESSING → DOWNLOADED`
- Downloads via `sftp.getfo()` into `BytesIO` buffer; writes to ABFSS using Hadoop `FileSystem` API
- Failed downloads: registry set to `FAILED` with full error message; other files continue

### 01_parse_files — Type-Aware Parser

Routes each file by type (patterns matched in specificity order):

| Pattern | Type | Target |
|---------|------|--------|
| `*.ingestion.error.csv.bz2` | `INGESTION_ERROR` | `cat_enriched_errors` |
| `*.linkage.error_*.csv.bz2` | `LINKAGE_ERROR` | `cat_linkage_errors` |
| `*.DEL.csv.bz2` | `DELETE` | `cat_raw_submissions` (flagged) |
| `*.ack.csv` | `ACK` | `cat_meta_feedback` |
| `*.integrity.csv` | `INTEGRITY` | `cat_meta_feedback` |
| `*.ingestion.csv` | `INGESTION_META` | `cat_meta_feedback` |
| `*.csv.bz2` (catch-all) | `SUBMISSION` | `cat_raw_submissions` |

**Meta file parsing** uses positional indexing validated against real 2026-04-27 production samples.
Positional layout (see `data_flow.md` for full table):
- `[0–8]` standard fields; `[9]` severity; `[10]` cat_error_code; `[11]` error_file_name;
  `[12]` error_count; `[16]` total_records_count.
- `safe_get(lst, idx)` helper returns `None` for out-of-bounds rather than raising `IndexError`.

**Error file parsing** — Phase 1 design:
- Only columns 0–2 are structured: `error_code`, `action_type`, `error_roe_id`
- Everything from column 3 onward is joined and stored as `raw_record STRING`
- `event_type = raw_record.split(',')[1]` — the `actionType` of the original CAT record
- This avoids brittle per-event-type schema coupling (Phase 2 concern)

**Submission files** stored as raw decompressed lines. Full event-type schema parsing is Phase 2.

### 02_enrich_errors — Enrichment & Trade Status

**Dictionary bootstrap:**
- Reads `cat_error_dictionary_full_v4_1_0.json` from ABFSS config path
- 367 codes covering all CAT stages: DATA_INGESTION, FILE_INTEGRITY, EXCHANGE_LINKAGE, etc.
- Stage → category mapping (hardcoded in pipeline config, not in data):

  | CAT Stage | Category |
  |-----------|----------|
  | DATA_INGESTION, FDID_VALIDATION | Ingestion |
  | FILE_INTEGRITY | Integrity |
  | EXCHANGE_LINKAGE, EXCHANGE_NAMED_LINKAGE, TRADE_LINKAGE, TRADE_NAMED_LINKAGE, INTRA_LINKAGE, INTERFIRM_SENDER, INTERFIRM_RECEIVER | Linkage |
  | WARNING | Warning |

**Error enrichment:**
- `LEFT JOIN` on `error_code` against dictionary
- Missing codes: `coalesce(description, 'UNKNOWN_ERROR_CODE')` — non-fatal
- Delta MERGE updates enrichment columns on `error_record_id` / `linkage_error_id`

**Trade status:**
- REJECTED: all `error_roe_id` values from both error tables → one row per rejected record
- ACCEPTED summary: one row per submission file, count from `total_records - error_count`
- Both upserted via Delta MERGE with natural key deduplication

### 03_monitoring — Operations Dashboard

Read-only; queries all tables directly:
1. File registry status breakdown
2. Failed files requiring attention
3. Meta feedback stage completion rates
4. Reconciliation by trade date (submitted / errors / accepted / error rate)
5. Top 25 error codes with descriptions
6. Trade status by trade date and category
7. Recent pipeline runs (configurable lookback)
8. Pipeline health KPIs (summary counts)
9. Late-arriving file detection (> T+3)
10. Error dictionary coverage check

---

## Dependency and Failure Isolation

```
sftp_pull ──→ parse_files ──→ enrich_errors ──→ monitoring
    ↓               ↓               ↓
  FAILED          FAILED          FAILED
  (logged,        (file-level     (logged,
  job retries     isolation,      pipeline
  2 times)        other files     continues)
                  continue)
```

A failure in one file never stops processing of other files in the same run.

---

## Cluster Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Spark version | 14.3.x LTS | Production-stable LTS release |
| Node type | Standard_DS3_v2 | 14 GB RAM, 4 vCPUs — sufficient for hourly micro-batches |
| Workers | 2 | Parallelism for multi-file runs; scale up for backfills |
| `shuffle.partitions` | 8 | Right-sized for hourly batch volume |
| `delta.schema.autoMerge` | true | Safe schema evolution without breaking writes |
| Auto-terminate | 20 min | Cost control between hourly runs |
| Library | `paramiko >= 3.4.0` | SFTP client (PyPI, per-job cluster library) |

---

## Security Design

- SSH private key in Databricks secrets exclusively — never in code, config, or logs
- ABFSS access via service principal `cat-pipeline-sp` with `Storage Blob Data Contributor`
- Job `run_as` set to service principal identity (not a user)
- Secret scope `regtech-ops` scoped to the pipeline service principal
- All notebook `dbutils.secrets.get()` calls fail loudly if the secret is missing
