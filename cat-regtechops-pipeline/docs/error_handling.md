# Error handling

## Meta feedback vs error files

- **Meta files** (`*.ack.csv`, `*.integrity.csv`, `*.ingestion.csv`) describe pipeline stages for a referenced submission filename. They are **not** trade rows. Parsing stores the full line and selected positional fields in `bi_output_regtechops_cat_meta_feedback`.
- **Error files** contain **only rejected** trade records plus leading error metadata. They are parsed minimally (three leading columns + `raw_record`) into `bi_output_regtechops_cat_linkage_errors` regardless of whether the vendor named the file `ingestion.error` or `linkage.error_*`.

## Dictionary enrichment

- Join key: `trim(linkage_errors.error_code)` = `trim(cast(dictionary.error_code as string))`.
- If no dictionary row matches:
  - `error_description = 'UNKNOWN_ERROR_CODE'` (literal sentinel required by the business rule),
  - `error_category = 'Unknown'`,
  - `processing_stage = 'UNKNOWN_STAGE'`,
  - `dictionary_hit = false`.
- The notebooks **never** embed vendor error text for known codes; all known text comes from `bi_output_regtechops_cat_error_dictionary`.

## Category mapping (load-time)

Dictionary JSON supplies `stage` per Appendix E. Loader maps to `error_category` as:

- `WARNING` → `Warning`
- Stage contains `LINKAGE` → `Linkage`
- Stage contains `INTEGRITY` or equals `FILE_INTEGRITY` → `Integrity`
- Stage contains `INGESTION`, equals `DATA_INGESTION`, or equals `FDID_VALIDATION` → `Ingestion`
- Otherwise → `Ingestion` (conservative default)

## Parser resilience

- Submission lines use UTF-8 with `errors='replace'` when reading text.
- Error rows with fewer than four logical segments still produce a row when the line is non-empty (empty tails become blank strings).
- Unknown file extensions are skipped at SFTP registration time.

## Job failure policy

- `00` raises on SFTP failure after logging `FAILED` process log entry.
- `01` aggregates per-file failures; if any file fails, the notebook raises after logging.
- `02` logs and raises on dictionary or merge errors so `03` does not mask upstream breakage.
