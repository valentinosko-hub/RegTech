# CAT RegTechOps Data Flow

## 1. End-to-End Flow
1. `00_sftp_pull` lists `/cat` on SFTP.
2. New files (by fingerprint) are registered in `bi_output_regtechops_cat_file_registry`.
3. Files are copied to ABFSS landing.
4. `01_parse_files` reads pending landed files and writes:
   - `bi_output_regtechops_cat_meta_feedback`
   - `bi_output_regtechops_cat_raw_submissions`
   - `bi_output_regtechops_cat_linkage_errors`
5. `02_enrich_errors` enriches parsed errors using dictionary table and writes:
   - `bi_output_regtechops_cat_enriched_errors`
   - `bi_output_regtechops_cat_trade_status`
6. `03_monitoring` computes operational checks and writes to:
   - `bi_output_regtechops_cat_process_log`

## 2. File-Type Routing Rules
| Pattern | Route |
|---|---|
| `*.csv.bz2` | Raw submission table (unless `.error.` or `.DEL`) |
| `*.ack.csv` / `*.integrity.csv` / `*.ingestion.csv` | Meta feedback table |
| `*.ingestion.error.csv.bz2` / `*.linkage.error_*.csv.bz2` | Error table |
| `*.DEL.csv.bz2` | Raw submission table with delete source type |

## 3. Trade Date Derivation
- Regex: `_(\d{8})_` from filename.
- Trade date is stored as `DATE`.
- Processing timestamp is separate and never used as business date.

## 4. Lifecycle States
`DISCOVERED -> PROCESSING -> SUCCESS/FAILED` in file registry, with stage flags:
- `parse_status`: `PENDING/PROCESSING/SUCCESS/FAILED`
- `enrich_status`: `PENDING/PROCESSING/SUCCESS/FAILED`

## 5. Late Arrivals and Corrections
- New physical version of same filename (changed mtime/size) creates a new fingerprint.
- All historical versions remain in registry and downstream tables.
