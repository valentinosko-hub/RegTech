# CAT RegTechOps Pipeline — Reconciliation Logic

## Overview

Reconciliation answers three questions for each submission file and trade date:

1. **Were all files acknowledged?** — Do we have ACK feedback for every submission?
2. **What was accepted vs rejected?** — `accepted = total_submitted − error_count`
3. **Are any errors unenriched?** — Are all error codes matched in the dictionary?

---

## Reconciliation by Submission File

For each `.csv.bz2` submission file, the pipeline expects three meta feedback files:

| Stage | File suffix | What it confirms |
|-------|-------------|-----------------|
| `FILE_ACKNOWLEDGEMENT` | `.ack.csv` | CAT received the file |
| `FILE_INTEGRITY` | `.integrity.csv` | Checksum verified, header valid |
| `INGESTION` | `.ingestion.csv` | Records parsed; reports totals and error count |

A submission is considered **fully reconciled** when:
- All 3 meta stages are `Success`
- `error_count = 0` in the INGESTION row

A submission has **partial rejections** when:
- INGESTION status = `Failure`
- `error_count > 0`
- Corresponding `.ingestion.error.csv.bz2` is received and parsed

---

## Reconciliation by Trade Date

The view `v_cat_daily_reconciliation` aggregates across all files per trade date:

```sql
SELECT
    trade_date,
    SUM(total_records_count) AS total_submitted,
    SUM(error_count)         AS total_errors,
    SUM(total_records_count) - COALESCE(SUM(error_count), 0) AS total_accepted,
    ROUND(SUM(error_count) / SUM(total_records_count) * 100, 4) AS error_rate_pct
FROM bi_output_regtechops_cat_meta_feedback
WHERE stage = 'INGESTION'
GROUP BY trade_date;
```

---

## Record-Level Reconciliation (Phase 1)

In Phase 1, trade status is tracked at two levels:

### REJECTED records (record-level)
Every `error_roe_id` in `bi_output_regtechops_cat_enriched_errors` and
`bi_output_regtechops_cat_linkage_errors` is stored in `bi_output_regtechops_cat_trade_status`
with `status = 'REJECTED'`.

### ACCEPTED records (file-level summary, Phase 1)
One row per submission file with `status = 'ACCEPTED'` and
`error_description = 'Accepted: N of M records'`.

In Phase 2 this becomes one row per accepted ROEID after full submission parsing.

### Query: Trade Status for a Trade Date

```sql
SELECT
    trade_date,
    status,
    COUNT(*) AS record_count
FROM regtech_ops_stg.bi_output_regtechops_cat_trade_status
WHERE trade_date = '2026-04-27'
GROUP BY trade_date, status;
```

---

## Late-Arriving File Reconciliation

CAT's SFTP server may deliver feedback files hours or days after the submission.
The pipeline is designed for this:

- Files are detected by comparing SFTP directory listing against the registry
- Every hourly run picks up any new files since the last run
- Late error files (arriving after T+1) are reconciled normally when detected
- The `v_cat_late_arriving_files` view identifies files discovered > T+3

Example scenario:

```
2026-04-27  17:00  Submission uploaded to CAT SFTP by eToro
2026-04-28  01:03  CAT delivers: 000001.ack.csv, 000001.integrity.csv, 000001.ingestion.csv
                   Pipeline run at 02:00 picks these up → all Success, 14373 records
2026-04-28  11:52  CAT delivers: 000002.ingestion.csv (Failure, 84 errors)
                   Pipeline run at 12:00 picks this up
2026-04-28  11:55  CAT delivers: 000002.ingestion.error.csv.bz2
                   Pipeline run at 13:00 picks this up → 84 rejected records enriched
```

---

## Corrected File Handling

When eToro submits a corrected file (same trade date, new sequence number), it arrives as a
new file name on SFTP (e.g. `...000003.csv.bz2`) and is treated as a brand-new submission.
The original file and its errors remain in the tables. No data is overwritten.

The `v_cat_daily_reconciliation` view automatically includes the corrected file's totals.

---

## DELETE File Handling

`.DEL.csv.bz2` files indicate records to be retracted. In Phase 1:
- DEL records are stored in `bi_output_regtechops_cat_raw_submissions` with prefix `DELETE_MARKER|`
- They do NOT trigger removal of existing submission records (immutable history)
- Phase 2 will implement full deletion reconciliation

---

## Reconciliation Completeness Checklist

For each trade date, full reconciliation requires:

| Check | Query target | Expected result |
|-------|-------------|-----------------|
| All submissions acknowledged | `v_cat_file_pipeline_status` | `ack_status = 'Success'` for all files |
| All submissions integrity-checked | `v_cat_file_pipeline_status` | `integrity_status = 'Success'` for all files |
| All ingestion feedback received | `v_cat_file_pipeline_status` | `ingestion_status IS NOT NULL` for all files |
| Error files received for all failures | `cat_file_registry` | INGESTION_ERROR file in SUCCESS status for each Failure ingestion |
| All errors enriched | `cat_enriched_errors`, `cat_linkage_errors` | `error_description IS NOT NULL` for all rows |
| No unknown error codes | `v_cat_top_errors` | No `UNKNOWN_ERROR_CODE` descriptions |

---

## Sample Reconciliation Numbers (2026-04-27 batch)

From the three sample files provided:

| File seq | Total records | Error count | Accepted | Status |
|----------|--------------|-------------|----------|--------|
| 000001 | 14,373 | 0 | 14,373 | Success |
| 000002 | 5,373 | 84 | 5,289 | Failure |
| 000003 | 84 | 0 | 84 | Success |
| **Total** | **19,830** | **84** | **19,746** | |

Note: File 000003 with 84 records likely represents the corrected resubmission of the 84 records
that were rejected from file 000002. This is a common CAT workflow pattern.

Error rate for 2026-04-27: **84 / 19,830 = 0.4236%**
