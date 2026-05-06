# CAT Reconciliation

## Business Rule

There is no CAT accepted-records file.

* Submission files contain all submitted records.
* Ingestion and linkage error files contain rejected records only.
* Accepted records are derived as `submission MINUS error records`.

## Implementation

`02_enrich_errors.py` builds `bi_output_regtechops_cat_trade_status` from:

* `bi_output_regtechops_cat_raw_submissions`
* `bi_output_regtechops_cat_enriched_errors`

Matching is by:

* `trade_date` from the filename; and
* `record_match_hash`, a CSV-aware canonical hash of the original submitted record.

The raw record text is still retained for audit. The matching hash is built by
generic CSV tokenization, quote handling, BOM/line-ending normalization, and
surrounding field whitespace trimming. This keeps Phase 1 schema-agnostic while
avoiding false accepts caused by harmless quote or whitespace differences between
submission and error files.

Status logic:

```sql
CASE
  WHEN matching error raw_record exists THEN 'REJECTED'
  ELSE 'ACCEPTED'
END
```

The output includes:

* trade_date
* event_type
* status
* error_code
* error_description

If multiple error codes exist for the same original record, the pipeline stores the semicolon-delimited set of codes and descriptions on the trade status row.

## Late Errors

Error files may arrive after submission files and after meta feedback. The reconciliation notebook scans all raw submissions and all enriched errors each run, then merges by `trade_status_key`. Previously accepted rows are updated to rejected when a late matching error arrives.

## Corrected Files

Corrected files are preserved because file identity includes remote path, size, and modified timestamp. A corrected file with the same name but different remote version gets a different `file_key` and is parsed as a new immutable file version.

## Idempotency

Each table uses deterministic keys:

* file registry: `file_key`
* raw submissions: `submission_record_key`
* raw errors: `error_record_key`
* enriched errors: `enriched_error_key`
* trade status: `trade_status_key`

Re-running a notebook merges the same keys and does not duplicate rows.
