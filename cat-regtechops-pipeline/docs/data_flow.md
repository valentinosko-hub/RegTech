# Data flow

## Source files (canonical naming)

Examples mirrored in `resources/`:

- `93007_ETOR_20260427_Group1_OrderEvents_000001.ingestion.csv` — INGESTION meta row; `Failure` path references `*.ingestion.error.csv.bz2` with counts (sample `000002`).
- `93007_ETOR_20260427_Group1_OrderEvents_000001.ack.csv` — FILE_ACKNOWLEDGEMENT stage.
- `93007_ETOR_20260427_Group1_OrderEvents_000001.integrity.csv` — FILE_INTEGRITY stage.

## Classification (`file_kind`)

| Pattern | `file_kind` | Parser |
|---------|-------------|--------|
| `*.csv.bz2` not containing `.error.` | `SUBMISSION` | bz2 text lines → `bi_output_regtechops_cat_raw_submissions` |
| `*.DEL.csv.bz2` | `DELETE_SUBMISSION` | same as submission (raw lines retained) |
| `*.ack.csv` | `META_ACK` | positional CSV lines → `bi_output_regtechops_cat_meta_feedback` (`meta_subtype=ACK`) |
| `*.integrity.csv` | `META_INTEGRITY` | meta table (`INTEGRITY`) |
| `*.ingestion.csv` | `META_INGESTION` | meta table (`INGESTION`) |
| `*.ingestion.error.csv.bz2` | `ERROR_INGESTION` | first three CSV fields + remainder → `bi_output_regtechops_cat_linkage_errors` (`error_file_type=INGESTION`) |
| `*.linkage.error_*.csv.bz2` | `ERROR_LINKAGE` | same target table (`error_file_type=LINKAGE`) |

Anything outside these patterns is ignored by SFTP pull (not registered).

## Meta positional mapping

Meta lines are split on commas into arrays; the parser maps:

- Indices 0–11 per CAT positional layout (version through `error_count`).
- `total_records_count`: index 14 when populated; if blank, the parser uses the **last numeric tail** on the line (covers sample `000001` ingestion where the count is the trailing field).

The full original line is always stored in `raw_meta_line`.

## Error file mapping

Each non-empty line is split **at most three commas** so the remainder preserves inner commas:

1. `error_code`
2. `action_type`
3. `errorROEID`
4. `raw_record` (string tail)

`event_type` is `split(raw_record, ',')[1]` (second field) when present.

## Dictionary

Bundled JSON: `resources/cat_error_dictionary_full_v4_1_0.json` (CAT v4.1.0 r15 Appendix E extract). Runtime path is the widget `error_dictionary_path` (job default `dbfs:/FileStore/regtech/cat_error_dictionary_full_v4_1_0.json` — upload from `resources/` during deployment).

## Storage layout

All tables are created by `sql/create_tables.sql` with `USING DELTA` and explicit `LOCATION` under  
`abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/<folder>/`.
