# CAT RegTechOps Pipeline — Data Flow

## End-to-End Data Flow

```
CAT SFTP                 ABFSS Landing             Delta Tables
transfer.s3.com/cat      sftp_landing/             regtech_ops_stg.*
───────────────────      ────────────────          ─────────────────────
                                                   
*.csv.bz2  ──────────→  {td}/{file}.csv.bz2 ──→  cat_raw_submissions
                                                        (raw lines)
                                                   
*.ack.csv  ──────────→  {td}/{file}.ack.csv  ──→  cat_meta_feedback
                                                        (stage=ACK)
                                                   
*.integrity.csv ──────→  {td}/{file}.int.csv ──→  cat_meta_feedback
                                                        (stage=INTEGRITY)
                                                   
*.ingestion.csv  ─────→  {td}/{file}.ing.csv ──→  cat_meta_feedback
                                                        (stage=INGESTION)
                                                        ↓
                                               total_records, error_count
                                                        ↓
                                               → cat_trade_status
                                                   (ACCEPTED summary)
                                                   
*.ingestion.error.       {td}/{file}.err.bz2 ──→  cat_enriched_errors
  csv.bz2  ─────────→                               (error_code,
                                                      action_type,
                                                      error_roe_id,
                                                      raw_record,
                                                      event_type)
                                                        ↓ join
                                               cat_error_dictionary
                                                        ↓
                                               cat_enriched_errors
                                                   (+ description,
                                                      category,
                                                      stage)
                                                        ↓
                                               → cat_trade_status
                                                   (REJECTED rows)
                                                   
*.linkage.error_*.       {td}/{file}.lnk.bz2 ──→  cat_linkage_errors
  csv.bz2  ─────────→                               (same structure)
                                                        ↓ join
                                               cat_error_dictionary
                                                        ↓
                                               → cat_trade_status
                                                   (REJECTED rows)
                                                   
*.DEL.csv.bz2  ───────→  {td}/{file}.DEL.bz2 ──→  cat_raw_submissions
                                                     (DELETE_MARKER|)
```

---

## File Registry Lifecycle

Every file seen on SFTP passes through these states:

```
DISCOVERED → PROCESSING → DOWNLOADED → [parse] → SUCCESS
                   ↓                       ↓
                FAILED ←─────────────── FAILED
                   ↑
            (retry on next run)
```

| Status | Meaning |
|--------|---------|
| `DISCOVERED` | File listed on SFTP, not yet downloaded |
| `PROCESSING` | Download or parse in progress |
| `DOWNLOADED` | File is on ABFSS, awaiting parse |
| `SUCCESS` | Fully parsed and written to target table |
| `FAILED` | Error in download or parse; `error_message` is populated |

---

## Trade Date Logic

Trade date is embedded in the filename:

```
93007_ETOR_20260427_Group1_OrderEvents_000001.csv.bz2
              ↑
         trade_date = 2026-04-27
```

The upload date (e.g. 2026-04-28 for Monday delivery of Friday trades) is stored in the meta
feedback files as `receipt_timestamp` and `stage_complete_timestamp`. It is **never** used as
the business date.

### US Weekend / Holiday Handling

CAT does not adjust filenames for weekends. A Friday submission arriving Monday will have
`trade_date = Friday`. The pipeline stores `trade_date` as parsed from the filename and makes
no calendar adjustments. Downstream business logic should apply calendar rules as needed.

---

## File Naming Convention

```
{submitter}_{reporter}_{YYYYMMDD}_{group}_{event_type}_{sequence}.{extension}

Examples:
  93007_ETOR_20260427_Group1_OrderEvents_000001.csv.bz2          ← submission
  93007_ETOR_20260427_Group1_OrderEvents_000001.ack.csv          ← ACK
  93007_ETOR_20260427_Group1_OrderEvents_000001.integrity.csv    ← integrity
  93007_ETOR_20260427_Group1_OrderEvents_000001.ingestion.csv    ← ingestion meta
  93007_ETOR_20260427_Group1_OrderEvents_000002.ingestion.error.csv.bz2  ← error
  93007_ETOR_20260427_Group1_OrderEvents_000003.linkage.error_1.csv.bz2  ← linkage
  93007_ETOR_20260427_Group1_OrderEvents_000002.DEL.csv.bz2      ← delete
```

Parsing:
- `submitter` = token[0] = `93007`
- `reporter`  = token[1] = `ETOR`
- `trade_date` = token[2] = `20260427`

---

## Meta File Column Layout

Verified against real production files (2026-04-27 batch, spec v4.1.0):

```
Index  Field                        Example (success)            Example (failure)
─────  ──────────────────────────── ────────────────────────     ────────────────────
[0]    version                      4.1.0                        4.1.0
[1]    submitter                    93007                        93007
[2]    reporter                     ETOR                         ETOR
[3]    file_date (trade_date)       20260427                     20260427
[4]    submission_file_name         ...000001.csv.bz2            ...000002.csv.bz2
[5]    receipt_timestamp            20260428T010340.119000000    20260428T115206.174000000
[6]    stage                        INGESTION                    INGESTION
[7]    stage_complete_timestamp     20260428T010658.535000000    20260428T115458.689000000
[8]    status                       Success                      Failure
[9]    severity                     (empty)                      Error
[10]   cat_error_code               (empty)                      (empty)
[11]   error_file_name              (empty)                      ...000002.ingestion.error.csv.bz2
[12]   error_count                  0                            84
[13]   (reserved)                   (empty)                      (empty)
[14]   (reserved)                   (empty)                      (empty)
[15]   (reserved)                   (empty)                      (empty)
[16]   total_records_count          14373                        5373
```

---

## Error File Column Layout

CAT error files have NO fixed schema. Only the first 3 columns are structured:

```
error_code, action_type, errorROEID, <original CAT record as remaining columns>
```

| Column | Name | Description |
|--------|------|-------------|
| 0 | `error_code` | Numeric CAT error code (e.g. `2027`) |
| 1 | `action_type` | Record action type (NEW / RPR / CANCEL) |
| 2 | `error_roe_id` | ROEID of the rejected record |
| 3+ | `raw_record` | Original CAT record joined back with commas |

`event_type` is extracted as `raw_record.split(',')[1]` — the `actionType` of the original event.

---

## Accepted Records Formula

```
Accepted records = total_records_count (from ingestion.csv) 
                 − error_count (from ingestion.csv)
```

There is **no** separate accepted-records file. The ingestion meta feedback file is the only
source for total and error counts.

Phase 1 stores a single ACCEPTED summary row per submission file.
Phase 2 will store individual ACCEPTED rows by joining submission records against error ROEIDs.
