# CAT RegTechOps Pipeline Overview

## 1. Purpose
This pipeline ingests CAT files from `transfer.s3.com:/cat`, persists all payloads as raw immutable history, enriches CAT errors from the approved CAT v4.1.0 r15 dictionary, and reconciles accepted/rejected trade outcomes at hourly frequency.

## 2. Scope
- **In scope:** SFTP file discovery, idempotent ingestion, metadata capture, error enrichment, trade status derivation, monitoring.
- **Out of scope (Phase 2 only):** event-type-aware full schema parsing and schema registry implementation.

## 3. Mandatory Platform Contract
- Schema: `regtech_ops_stg`
- Table prefix: `bi_output_regtechops_`
- Storage root:  
  `abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/`
- All CAT tables are **EXTERNAL DELTA** with explicit `LOCATION`.

## 4. Business Process Summary
1. Pull new CAT files hourly from SFTP.
2. Register files with lifecycle state transitions (`DISCOVERED -> PROCESSING -> SUCCESS/FAILED`).
3. Parse files by type:
   - Submission / delete files as raw records.
   - Meta feedback files by positional index.
   - Error files by first 3 fields + raw tail.
4. Enrich errors from `bi_output_regtechops_cat_error_dictionary`.
5. Produce `bi_output_regtechops_cat_trade_status`:
   - `REJECTED` when raw record exists in an error file.
   - `ACCEPTED` otherwise.
6. Publish monitoring outputs and process logs.

## 5. Inputs
- Submission: `*.csv.bz2`
- Meta feedback (no header): `*.ack.csv`, `*.integrity.csv`, `*.ingestion.csv`
- Errors: `*.ingestion.error.csv.bz2`, `*.linkage.error_*.csv.bz2`
- Deletes: `*.DEL.csv.bz2`
- Error dictionary JSON: `cat_error_dictionary_full_v4_1_0.json`

## 6. Trade Date Rule
Trade date is always extracted from the filename (`_(\d{8})_`) and treated as the business date. Arrival/upload timestamp is never used as trade date.

