# CAT Pipeline Error Handling

## 1. Error Categories
1. **Transport errors:** SFTP connectivity, authentication, remote read failures.
2. **Parse errors:** malformed files, unsupported file structure.
3. **Enrichment errors:** dictionary load/join issues.
4. **Operational errors:** long-running processing states, unknown error code spikes.

## 2. File Lifecycle Error Control
- Lifecycle status is tracked in `bi_output_regtechops_cat_file_registry`.
- State transitions:
  - `DISCOVERED`
  - `PROCESSING`
  - `SUCCESS` or `FAILED`
- Parse and enrich stages have independent status columns, enabling targeted reruns without data loss.

## 3. Dictionary Enrichment Error Control
- Error dictionary table `bi_output_regtechops_cat_error_dictionary` is the single source of truth.
- Enrichment join key: `error_code`.
- Missing dictionary match behavior:
  - `error_description = 'UNKNOWN_ERROR_CODE'`
  - `error_category = 'UNKNOWN'`
  - `processing_stage = 'UNKNOWN'`
- Pipeline does not fail for unknown codes.

## 4. Idempotency and Duplicate Protection
- File-level: fingerprint-based anti-duplication.
- Record-level: deterministic hash IDs with Delta `MERGE`.
- Reruns are safe; duplicate raw/enriched/trade-status rows are not created.

## 5. Alertable Conditions
- Any notebook write with `status = FAILED` in `bi_output_regtechops_cat_process_log`.
- Files stuck in `PROCESSING` state for >2 hours.
- Unknown error code counts increasing unexpectedly.

## 6. Escalation
1. Resolve immediate operational issue (credentials/network/schema break).
2. Rerun failed task only.
3. Validate downstream tables and views.
4. If reconciliation mismatch remains, trigger manual investigation against raw submission/error payloads.
