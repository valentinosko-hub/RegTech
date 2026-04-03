# Trade Reporting Reconciliation Architecture (Updated Detailed Version)

Last updated: 2026-03-18

This document consolidates architecture and data-source details from the final data source inventory and the latest repository diagrams under:

- `regtech-automation-project/diagrams/`

> **INFO**  
> This page is the repository equivalent of a Confluence architecture page, maintained alongside the working diagrams.

---

## 1) Scope and reporting models

Regulations and reporting models covered:

- MiFID (EU/UK) - ARM-Based
- EMIR (EU/UK) - TR-Based
- ASIC - TR-Based
- CAT (US) - event-driven
- SFTR - direct to DTCC
- LTR - manual/transitional
- LP delegated reporting
- APA (MiFID) real-time publication

### 1.1 Quick model summary

| Model | Regulation | Operating pattern | Submitted channel | Actual-state source |
|---|---|---|---|---|
| MiFID | MiFID (EU/UK) | ARM-based | Cappitech -> TRAX (ARM path) | TRAX ARM response files |
| EMIR | EMIR (EU/UK) | TR-based | Cappitech -> Regis-TR/DTCC | TR response files |
| ASIC | ASIC | TR-based | Cappitech -> Regis-TR/DTCC | TR response files |
| CAT | CAT (US) | Event-driven | S3 exchange -> FINRA CAT | CAT feedback files (SharePoint) |
| SFTR | SFTR | Direct-to-TR | Direct DTCC XML/SFTP | DTCC acknowledgements/rejections |
| LTR | LTR | Manual/transitional | FIPS VM -> CME/CFTC | Acknowledgement + transfer tracking |
| LP delegated | LP delegated | Two-stage control | LP submits to REGIS/UNAVISTA/DTCC | TR responses by LP mapping |
| APA | APA (MiFID) | Real-time publication | APA Event Hub -> TradeEcho | TradeEcho SFTP confirmations |

---

## 2) Control framework and state model

The reconciliation framework compares independent views of the same regulatory obligation:

- **Expected**: regulatory baseline produced by internal reporting logic
- **Submitted**: what was actually sent via vendor/channel
- **Actual**: regulator/TR/APA feedback or response evidence

For LP delegated reporting, control is explicitly split into two stages:

1. **Stage 1**: Internal vs LP alignment (execution/position consistency)
2. **Stage 2**: LP submitted vs TR actual validation

For direct reporting (MiFID/EMIR/ASIC), Operational/BI is modeled as a **completeness comparison source**, not as a direct reporting-table generation step.

> **DECISION**  
> Operational / BI is treated as an independent comparison baseline for completeness controls in direct-reporting models (MiFID/EMIR/ASIC). It is not the table-creation pipeline for regulatory outputs.

---

## 3) Cross-cutting data-source inventory (platform view)

### 3.1 Internal source and transformation platforms

- **Synapse DWH**
  - Server: `SYNAPSE-DWH-PROD`
  - Database: `sql_dp_prod_we`
  - Common schema/tables used across models:
    - `DWH_dbo.Dim_Position`
    - `DWH_dbo.Dim_Instrument`
    - `DWH_dbo.Fact_SnapshotCustomer`

- **SQL Server RegReportDB**
  - Server: `AZR-WE-BI-21`
  - Database: `RegReportDB`
  - Role: source tables, `ext_*` transformations, expected reporting baselines

- **Hedge execution SQL**
  - Server: `AZR-W-REAL-DB-2-BIDBUser`
  - Database: `etoro`
  - Schema/table: `Hedge.ExecutionLog`

- **Databricks**
  - Key catalogs: `main.general`, `main.bi_db`, `main.regtech_stg`, `main.regtech`, `main.dealing`
  - Role: ingestion (bronze), harmonization (silver), recon-ready views (gold), response tracking

### 3.2 External submission and feedback channels

- Cappitech (submission path split by model: TRAX for MiFID ARM; REGIS/DTCC for TR models)
- S3 (CAT submission exchange)
- TradeEcho/LSEG (APA)
- DTCC (SFTR direct and TR responses by model)
- CME/CFTC via FIPS VM (LTR submission path)
- SharePoint (CAT feedback files, eToro USA)

> **WARNING**  
> External systems (TRAX, Regis-TR, DTCC, FINRA CAT, TradeEcho, CME/CFTC) are submission/feedback endpoints, not table-level source systems under internal ownership.

---

## 4) Detailed data sources by reporting model

### 4.0 Read guide (applies to every model)

Use each model section as:

1. **Core internal sources** (system-of-record inputs)
2. **Transformations / expected baseline** (golden source expectation)
3. **Submitted / actual channels** (what was sent vs what was acknowledged/returned)

## 4.1 MiFID (EU/UK) - ARM-Based

### Core internal sources

- Synapse DWH completeness-control baseline:
  - `Dim_Position`, `Dim_Instrument`, `Fact_SnapshotCustomer`
- Hedge execution:
  - `etoro.Hedge.ExecutionLog`
- RegReportDB source and reference domains:
  - `FIRDS_*`, `FCA_*`, `MIFID2_*`, shared enrichment references

### Transformations / expected baseline

- Upstream transforms:
  - `MIFID2_ext_*`, shared `Reg_Ext_*`
- Expected reports:
  - `MIFID2_Report`
  - `MIFID2_Hedge_Report`
  - `MIFID2_ETORO_Report`
  - `MIFID2_ME_Report`

### Submitted / actual channels

- Submitted: Cappitech files to TRAX ARM endpoints (MiFID EU/UK flows)
- Actual: ARM response files from TRAX (where ingested), represented in Databricks response layers

---

## 4.2 EMIR (EU/UK) - TR-Based

### Core internal sources

- Synapse DWH completeness-control baseline
- Hedge execution (`Hedge.ExecutionLog`)
- RegReportDB EMIR source tables:
  - `EMIR2_Customer`
  - `EMIR2_InstrumentMetaData`
  - related EMIR source domains
- UPI/reference enrichment:
  - ANNA DSB (`AZR-WE-BI-20`, `RTS`, `UPI_*` tables)

### Transformations / expected baseline

- Upstream transforms:
  - `EMIR2_ext_*`
  - selected shared `Reg_Ext_*`
- Expected reports:
  - `EMIR2_Refit_Report`
  - `EMIR2_Refit_Report_Daily`
  - `EMIR2_Report_Refit_Collateral`
  - `EMIR3_*` report family (EU/UK variants)

### Submitted / actual channels

- Submitted: Cappitech -> Regis-TR / DTCC (by flow)
- Actual: TR responses, with REGIS represented as live in current ingestion and DTCC coverage depending on flow

---

## 4.3 ASIC - TR-Based

### Core internal sources

- Synapse DWH completeness-control baseline
- Hedge execution (`Hedge.ExecutionLog`)
- RegReportDB ASIC source domains:
  - `ASIC2_Customer_PositionReport`
  - `ASIC2_Daily_Prices`
  - `ASIC2_InstrumentMetaData`
  - `ASIC2_Positions*`

### Transformations / expected baseline

- Upstream transforms:
  - `ASIC2_ext_Position`
  - `ASIC2_ext_Customer`
  - `ASIC2_Reg_Ext_DailyMaxPrices`
  - `ASIC2_ext_DWH_V_Liabilities`
  - `ASIC2_ext_OpenPositions_PositionsReport`
- Expected reports:
  - `ASIC2_Transactions`
  - `ASIC2_Transactions_Hedge`
  - `ASIC2_Positions_AGG`
  - `ASIC2_Positions_AGG_Hedge`
  - `ASIC2_Collateral`

### Submitted / actual channels

- Submitted: Cappitech vendor files
- Actual: TR response files by model path

---

## 4.4 CAT (US) - event-driven

### Core internal sources

- Databricks operational/log tables (`main.general`, `main.bi_db`) for order lifecycle:
  - order open/close history
  - execution plans
  - executed orders
- Upstream US transforms:
  - SQL Server `Reg_Ext_US_*`
  - Databricks `main.regtech_stg.reg_ext_us_*` and related histories

### Expected / submitted / actual

- Expected baseline:
  - SQL Server `Reg_US_*` (e.g., `Reg_US_COrders`, `Reg_US_NOrders`, etc.)
  - mirrored in `main.regtech.gold_regreportdb_prod_dbo_reg_us_*`
- Submitted:
  - S3 vendor exchange to FINRA CAT
- Actual:
  - CAT feedback files via eToro USA SharePoint path

---

## 4.5 SFTR - direct to DTCC

### Core internal sources

- Databricks `main.general` vision snapshots:
  - `main.general.gold_vision_etoro`
  - `main.general.gold_visionet_r002_eod_trades_et`

### Expected / submitted / actual

- Expected:
  - lifecycle derivation dataset in `main.regtech_stg.bronze_sftr_report`
- Submitted:
  - direct SFTR XML to DTCC (no Cappitech vendor)
- Actual:
  - DTCC acknowledgements/rejections/validation feedback ingested via SFTP

---

## 4.6 LTR - manual/transitional

### Core internal sources

- Position baseline:
  - `main.dealing.gold_sql_dp_prod_we_dealing_dbo_dealing_marex_recon_eodholdings_futures`
- Customer ownership:
  - `main.bi_output_stg.customer_radar_view_dim_customer`
- Threshold logic:
  - CFTC threshold controls and aggregation logic

### Submitted / actual model

- Submitted:
  - LTR and 102A payloads via FIPS-enabled VM to CME/CFTC
- Actual (limited):
  - acknowledgement and transfer tracking, not full lifecycle state

### LTR tracking tables (Databricks, `main.regtech_stg`)

- `bronze_ltr_file_runs`
- `bronze_ltr_transfers`
- `bronze_ltr_cftc_thresholds`
- `bronze_ltr_ocr_102a_runs`
- `bronze_ltr_instrument_map`
- `bronze_ltr_responses`

---

## 4.7 LP delegated reporting

### Stage 1: internal vs LP alignment sources

- Internal DUCO views/tables:
  - `main.dealing.gold_sql_dp_prod_we_dealing_dbo_v_dealing_duco_eodrecon`
  - `main.dealing.gold_sql_dp_prod_we_dealing_dbo_dealing_duco_activityrecon`
- Synapse dealing reconciliation tables (examples):
  - `Dealing_IGReconTrades`
  - `Dealing_IGReconEODHolding`

### Stage 2: LP submitted vs TR actual sources

- LP provider tables in `Dealing_staging` (examples):
  - `LP_EdnF_*`
  - `LP_GS_*`
  - `LP_UBS_*`
  - `LP_IG_*`
  - `LP_SAXO_*`
- TR feedback paths:
  - REGIS (live ingestion)
  - UNAVISTA / DTCC (coverage depends on ingestion state by flow)

---

## 4.8 APA (MiFID) - real-time publication

### Core event sources

- Trading event stream (event-driven origin)
- Internal processing services -> APA Event Hub
- TradeEcho publication path

### Actual-state source

- TradeEcho SFTP confirmations in:
  - `main.regtech.bronze_tradeecho_responses`

### Completeness control baseline (added)

For completeness checks in APA flows, filtered comparison is performed against:

- `RegReportDB_Prod:MiFID.MIFID2_Report`
- `RegReportDB_Prod:MiFID.MIFID2_Hedge_Report`

> **INFO**  
> APA completeness checks rely on filtered alignment between APA event outcomes and MiFID reporting baselines above.

---

## 5) Current ingestion and coverage notes

- REGIS and TradeEcho response ingestion represented as active/live
- DTCC/TRAX/UNAVISTA represented as partial/pending by model flow
- LTR remains acknowledgement/transfer-led rather than full actual-state lifecycle
- Some shared reference assets include migration and data-quality caveats (e.g., partial migration of certain reference tables)

> **WARNING**  
> Coverage status can differ by model and endpoint; maintain model-level assumptions explicitly in reconciliations and operational runbooks.

---

## 6) Diagram index

### 6.1 Cross-model views

- Business flow by regulation:
  - `regtech-automation-project/diagrams/regtech-recon-business-architecture.md`
- Executive summary:
  - `regtech-automation-project/diagrams/regtech-recon-engine-exec-diagram.md`
- Detailed engineering:
  - `regtech-automation-project/diagrams/regtech-architecture-diagram.md`
- XML-converted technical view:
  - `regtech-automation-project/diagrams/trade-recon-architecture-v2-from-xml.md`
  - draw.io XML: `regtech-automation-project/diagrams/trade-recon-architecture-v2-from-mermaid.xml`

### 6.2 Per-reporting-model data-source diagrams

- Index: `regtech-automation-project/diagrams/reporting-model-data-source-flows.md`
- MiFID: `regtech-automation-project/diagrams/reporting-model-mifid-data-sources.md`
- EMIR: `regtech-automation-project/diagrams/reporting-model-emir-data-sources.md`
- ASIC: `regtech-automation-project/diagrams/reporting-model-asic-data-sources.md`
- CAT: `regtech-automation-project/diagrams/reporting-model-cat-data-sources.md`
- SFTR: `regtech-automation-project/diagrams/reporting-model-sftr-data-sources.md`
- LTR: `regtech-automation-project/diagrams/reporting-model-ltr-data-sources.md`
- LP delegated: `regtech-automation-project/diagrams/reporting-model-lp-delegated-data-sources.md`
- APA: `regtech-automation-project/diagrams/reporting-model-apa-data-sources.md`

