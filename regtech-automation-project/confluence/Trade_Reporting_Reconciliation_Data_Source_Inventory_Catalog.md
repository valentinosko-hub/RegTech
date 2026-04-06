# Step 2A - Data Source Inventory Catalog (Source Register)

Last updated: 2026-03-18  
Workstream: Data source inventory + field mapping matrix (REG-3279 Step 2)  
Owner: Valentinos Konstantinou

## 1) Purpose

Provide a complete and auditable catalog of data sources used by regulatory reconciliation controls.

This document is intentionally the **source register** artifact (Step 2A), not the field-level reconciliation matrix.

This artifact is structured to satisfy Step 2A acceptance criteria:
- inventory table completed,
- owners assigned,
- sample file/table references captured.

Detailed one-row-per-table coverage is documented in:
- `Trade_Reporting_Reconciliation_Data_Source_Inventory_Table_Level_Appendix.md`

## 1.1 What this artifact is and is not

This artifact **is**:
- a catalog of systems/tables/files/feeds in scope,
- an ownership and operational-metadata register,
- a migration and coverage tracker.

This artifact **is not**:
- a field-by-field reconciliation rule matrix,
- a source-to-report-to-response mapping at column level.

Those are documented in:
- `Trade_Reporting_Reconciliation_Field_Mapping_Matrix.md`

## 2) Inventory schema

Each source row includes:
- regulation/model usage,
- source type (internal/external),
- owner,
- format,
- frequency,
- storage location,
- migration state (legacy -> Azure/Databricks),
- sample reference.

## 3) Master source inventory

| Source ID | Type | Used by | Source/system | Owner | Format | Frequency | Storage / landing location | Migration state | Sample file/table reference | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| SRC-001 | Internal | MiFID/EMIR/ASIC | Synapse DWH (`SYNAPSE-DWH-PROD`) | Data Engineering + Ops | DB table | Daily | `sql_dp_prod_we.DWH_dbo` | Active (Azure) | `Dim_Position`, `Dim_Instrument`, `Fact_SnapshotCustomer` | Completeness comparison baseline |
| SRC-002 | Internal | MiFID/EMIR/ASIC | RegReportDB (`AZR-WE-BI-21`) | Reg Reporting Ops | DB table | Daily | SQL Server `RegReportDB` | Legacy SQL (active), mirrored selectively | `MIFID2_*`, `EMIR2_*`, `ASIC2_*`, `Reg_US_*` | Golden-source and staging families |
| SRC-003 | Internal | MiFID/EMIR/ASIC | Hedge execution DB (`AZR-W-REAL-DB-2-BIDBUser`) | Trading Tech + Ops | DB table | Intraday/daily | `etoro.Hedge.ExecutionLog` | Legacy SQL active | `Hedge.ExecutionLog` | Feeds expected-state generation |
| SRC-004 | Internal | EMIR/ASIC | Reference enrichment (ANNA DSB) | Reg Data Management | DB table | Daily | `AZR-WE-BI-20.RTS` | Active | `UPI_*`, instrument/reference tables | UPI and classification enrichment |
| SRC-005 | Internal | LP delegated | Synapse dealing recon tables/views | Dealing Ops + Data Eng | DB table/view | EOD | Synapse + `main.dealing` mirrors | Active | `v_dealing_duco_eodrecon`, `dealing_duco_activityrecon` | LP Stage 1 (internal vs LP) |
| SRC-006 | Internal | LP delegated | LP provider staging tables | Dealing Ops | DB table/file ingest | EOD | `Dealing_staging` + Databricks bronze | Active/partial by LP | `LP_EdnF_*`, `LP_GS_*`, `LP_UBS_*`, `LP_IG_*`, `LP_SAXO_*` | LP Stage 2 context |
| SRC-007 | Internal | CAT | Databricks order/event logs | US Ops + Data Eng | Delta table | Daily/intraday | `main.general`, `main.bi_db`, `main.regtech_stg` | Active (Azure/DBX) | `bronze_etoro_dwh_historyorderfor*`, `reg_ext_us_*` | Event-level control feeds |
| SRC-008 | Internal | SFTR | Vision snapshots and derived lifecycle layers | Reg Reporting Ops | Delta table/XML output | Daily | `main.general`, `main.regtech_stg.bronze_sftr_report` | Active | `gold_vision_etoro`, `gold_visionet_r002_eod_trades_et` | Direct DTCC reporting path |
| SRC-009 | Internal | LTR | Dealing futures holdings + ownership views | Ops + Compliance Reporting | Delta table/file | Daily | `main.dealing`, `main.bi_output_stg` | Active | `...dealing_marex_recon_eodholdings_futures`, `customer_radar_view_dim_customer` | Position/account and threshold controls |
| SRC-010 | Internal | APA | Trade event streams | Trading Tech + Reg Ops | Event stream | Near real-time | Event Hub + `main.regtech.bronze_tradeecho_responses` | Active | `...client_trade_evh`, `...finance_tcr_evh` | Publication control path |
| SRC-011 | External | MiFID | Cappitech submission outputs -> TRAX (ARM) | Reg Ops | File (CSV/XML by feed) | Daily/intraday | SFTP landing -> DBX bronze (planned/partial by feed) | Partial by flow | `bronze_cappitech_*` families | Submitted-state evidence |
| SRC-012 | External | EMIR | Cappitech -> Regis-TR submission/response | Reg Ops | File | Daily | SFTP -> DBX bronze | Active/partial by flow | `S030`, `S091`, `S092`, `S106`, `S107` patterns | TR response coverage strongest on REGIS |
| SRC-013 | External | ASIC/EMIR/SFTR | DTCC files (submission/response by model) | Reg Ops | File/XML | Daily | DTCC SFTP -> ingestion layers | Partial/pending by model flow | DTCC ack/reject response sets | Coverage differs by model |
| SRC-014 | External | LP delegated | UNAVISTA feedback files | Reg Ops | File | Daily | External endpoint, ingestion pending/partial | Partial | LP feedback extracts by LP/report | Not fully represented in ingestion yet |
| SRC-015 | External | CAT | S3 exchange + FINRA CAT feedback | US Ops | File | Daily | S3 transfer + SharePoint feedback landing | Active | CAT feedback files in eToro USA SharePoint | Event rejection/acceptance tracking |
| SRC-016 | External | APA | TradeEcho (LSEG) confirmations | Reg Ops | File | Near real-time/batch | SFTP `/Outgoing/SRR` -> DBX bronze | Active | `main.regtech.bronze_tradeecho_responses` | Actual-state evidence for APA |
| SRC-017 | External | LTR | CME/CFTC transfer acknowledgements | Ops + Compliance | File/log | Daily | FIPS VM transfer logs + DBX bronze LTR tables | Active, limited feedback model | `bronze_ltr_transfers`, `bronze_ltr_responses` | No full TR-style lifecycle responses |

## 3.1 Detailed table-level appendix

For the exhaustive table/view/feed list by model and flow stage, see:

- `Trade_Reporting_Reconciliation_Data_Source_Inventory_Table_Level_Appendix.md`

## 4) Field mapping matrix handoff

Field-level mapping and reconciliation rules are maintained in:

- `Trade_Reporting_Reconciliation_Field_Mapping_Matrix.md`

That matrix captures:
- source field,
- expected reporting field,
- submitted evidence field,
- actual response field,
- transform and validation logic,
- tolerance and exception treatment.

## 5) Data quality and migration notes

- Mixed ownership still exists between legacy SQL and Databricks layers.
- DTCC/TRAX/UNAVISTA ingestion coverage is not uniform across all flows.
- Manual sheet controls remain a residual governance risk until fully replaced.
- LTR actual-state evidence remains acknowledgement/transfer driven rather than full lifecycle response driven.

## 6) Acceptance criteria tracking (Step 2A)

- [x] Inventory table created and populated with current known sources
- [x] Owners assigned at source level (role-based; named owners can be added per squad)
- [x] Sample file/table references included
- [x] Scope boundary clarified: this page is catalog-only
- [x] Detailed table-level appendix linked and maintained
