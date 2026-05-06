# CAT Data Flow

## 1. SFTP discovery

`00_sftp_pull.py` connects to `transfer.s3.com:/cat` with connection type `SFTP`.
The private key is read from Databricks secret key `TR-S3-CAT-SSHKey` in the
configured secret scope.

The notebook lists files in `/cat`, classifies supported file names, and creates
an immutable `file_key` from:

* remote path
* file name
* remote size
* remote modified timestamp

This allows corrected files with the same name but different remote metadata to
be retained as separate file versions.

## 2. Landing

New file versions are written under:

`abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/_landing/cat/`

Each landed file is stored by file type, trade date, file key, and original file
name. The original suffix is preserved so Spark can decompress `.bz2` files.

## 3. Registry lifecycle

The lifecycle in `bi_output_regtechops_cat_file_registry` is:

1. `DISCOVERED`
2. `PROCESSING`
3. `SUCCESS` or `FAILED`

Every processing step also writes `bi_output_regtechops_cat_process_log`.

## 4. Raw parsing

`01_parse_files.py` parses only landed file versions that do not already have a
successful `01_parse_files` process-log entry.

### Meta feedback

Meta files have no header and are positional CSV:

| Position | Field |
| --- | --- |
| 0 | version |
| 1 | submitter |
| 2 | reporter |
| 3 | file_date |
| 4 | file_name |
| 5 | receipt_timestamp |
| 6 | stage |
| 7 | stage_complete_timestamp |
| 8 | status |
| 9 | severity |
| 10 | error_code |
| 11 | error_count |
| 14 | total_records_count |

The uploaded canonical examples include ingestion rows where the error file name
is at position 11, error count at position 12, and total records at position 16.
The implementation keeps the raw line and uses safe numeric coalescing to support
both the specified layout and the sample files.

### Error files

Error files are parsed only for:

1. `error_code`
2. `action_type`
3. `errorROEID`

The remaining text is stored as `raw_record`. Event type is extracted as the
second CSV field of `raw_record` with quote-aware parsing. This is event-type
agnostic and works for all CAT event types because the CAT event type position
is consistent while downstream event schemas differ.

### Data files

Submission and delete files are stored as raw records. No event schema is
enforced in Phase 1.

## 5. Enrichment

`02_enrich_errors.py` joins raw error rows to
`bi_output_regtechops_cat_error_dictionary` by `error_code`. Unknown codes are
retained with `error_description = 'UNKNOWN_ERROR_CODE'`.

## 6. Reconciliation

Trade status is derived from:

`raw submissions LEFT JOIN enriched errors`

on `trade_date` and `record_match_hash`, a SHA-256 hash over a CSV-canonicalized
record. This avoids false accepts/rejects caused by quoting, leading/trailing
field spaces, BOMs, or line-ending differences.

* match exists: `REJECTED`
* no match exists: `ACCEPTED`

Late-arriving errors are handled by rerunning the reconciliation over all raw
submissions and all enriched errors; the status table is merged idempotently.
