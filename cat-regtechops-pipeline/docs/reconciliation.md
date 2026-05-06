# CAT Reconciliation Logic

## 1. Core Rule
There is no accepted-records feedback file.  
Accepted status is derived using:

`ACCEPTED = SUBMISSION_RECORDS - ERROR_RECORDS`

## 2. Submission Dataset
- Source table: `regtech_ops_stg.bi_output_regtechops_cat_raw_submissions`
- Grain: one row per raw CAT submission record
- Key field: `raw_record_hash`

## 3. Error Dataset
- Source table: `regtech_ops_stg.bi_output_regtechops_cat_enriched_errors`
- Grain: one row per CAT rejected record
- Key field: `raw_record_hash`

## 4. Matching Strategy
Join submissions to enriched errors using:
- `trade_date`
- `raw_record_hash`

If at least one match exists, record is `REJECTED`. Otherwise, `ACCEPTED`.

## 5. Output Table
`regtech_ops_stg.bi_output_regtechops_cat_trade_status` columns:
- `trade_date`
- `event_type`
- `status` (`REJECTED` / `ACCEPTED`)
- `error_code`
- `error_description`
- audit columns (`created_ts`, `updated_ts`)

## 6. Late Error Handling
Late error files are ingested incrementally.  
When a newly arrived error matches an existing submission hash, future reconciliations classify that trade as `REJECTED`.
