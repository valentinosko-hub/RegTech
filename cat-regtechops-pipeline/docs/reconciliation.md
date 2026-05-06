# Reconciliation logic

## Business rule

There is **no** separate accepted-records file from the processor.

- **Submitted population**: every line in each `SUBMISSION` (and `DELETE_SUBMISSION`) file is stored in `bi_output_regtechops_cat_raw_submissions`.
- **Rejected population**: every line from error artefacts is stored in `bi_output_regtechops_cat_linkage_errors` and enriched in `bi_output_regtechops_cat_enriched_errors`.
- **Accepted trades** (Phase 1 definition): submission rows **not** present in the rejected population using the match rule below.

## Match rule (Phase 1)

`bi_output_regtechops_cat_trade_status` is derived as:

1. Build `rej` = distinct `trim(raw_record)` from `bi_output_regtechops_cat_enriched_errors`.
2. Left-join `bi_output_regtechops_cat_raw_submissions` to `rej` on `trim(raw_submissions.raw_record) = rej.raw_norm`.
3. If the join hits, `status = REJECTED` and `error_code` / `error_description` come from the aggregated error side (`min(error_code)` with paired description — operational tie-break only).
4. Else `status = ACCEPTED` with null error fields.

This uses the **exact original record text** as carried in CAT error files (the tail after the third comma) compared to the submission line text. Phase 2 may introduce structured keys (for example ROE identifiers) once schemas are enforced.

## Views

- `bi_output_regtechops_cat_vw_accepted_submissions` — joins `raw_submissions` to `trade_status` where `status = ACCEPTED`.
- `bi_output_regtechops_cat_vw_rejected_submissions` — joins where `status = REJECTED`.
- `bi_output_regtechops_cat_vw_file_health` — registry counts by `trade_date`, `registry_status`, `file_kind`.

## Late and corrected files

- **Late errors**: a new error row causes the next `02_enrich_errors` run to `MERGE` an existing `trade_status` row from `ACCEPTED` to `REJECTED`.
- **Corrected submissions**: a new submission filename (new `sftp_remote_path`) creates a new `file_registry_id` and new `raw_submission_id` values; history is retained (no overwrite deletes).

## Table design summary

| Table | Role |
|-------|------|
| `bi_output_regtechops_cat_file_registry` | SFTP inventory + lifecycle |
| `bi_output_regtechops_cat_meta_feedback` | ACK / integrity / ingestion meta rows |
| `bi_output_regtechops_cat_raw_submissions` | Raw submission / delete lines |
| `bi_output_regtechops_cat_linkage_errors` | Parsed error-file rows (ingestion + linkage) |
| `bi_output_regtechops_cat_error_dictionary` | Appendix E dictionary |
| `bi_output_regtechops_cat_enriched_errors` | Errors + dictionary attributes + `dictionary_hit` |
| `bi_output_regtechops_cat_trade_status` | Per submission line acceptance outcome |
| `bi_output_regtechops_cat_process_log` | Notebook-level run audit |

All include `created_ts` and `updated_ts` as required.
