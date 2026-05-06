# CAT Error Handling

## Error dictionary

`bi_output_regtechops_cat_error_dictionary` is the only approved source for CAT error descriptions, categories, and processing stages.

The dictionary loader reads the JSON supplied from CAT Specification v4.1.0 r15 and stores:

- `error_code`
- `error_description`
- `error_category`
- `processing_stage`
- `severity`
- source version/file metadata

No notebook hardcodes error descriptions.

## Unknown error codes

If an error file contains a code missing from the dictionary:

- the pipeline does not fail
- `error_description` is set to `UNKNOWN_ERROR_CODE`
- `error_category` and `processing_stage` remain null
- `03_monitoring` reports the code in the unknown-code summary

Set `fail_on_unknown_error_codes=true` in the monitoring task only when operations wants unknown codes to fail the job after data has landed.

## File failures

SFTP download failures update the registry row to `FAILED`, retain the exception message, and write a failed process-log row. A future run discovers the same immutable file version and can retry failed rows after remediation.

## Parser failures

Parser failures are file-scoped. Successful files remain committed through Delta merges. Failed files do not get a successful `01_parse_files` process-log row, so they remain eligible for reprocessing after the cause is fixed.

## Reconciliation failures

Reconciliation can be rerun safely. It rebuilds enriched errors and trade status from raw submission/error Delta tables and uses MERGE semantics to avoid duplicates.
