# Trade Reporting Reconciliation Architecture (Updated)

Last updated: 2026-03-18

This document consolidates the latest architecture and data-source updates reflected in repository diagrams under:

- `regtech-automation-project/diagrams/`

---

## 1) Scope

Regulations and reporting models covered:

- MiFID (EU/UK) - TR/ARM-based
- EMIR (EU/UK) - TR/ARM-based
- ASIC - TR/ARM-based
- CAT (US) - event-driven
- SFTR - direct to DTCC
- LTR - manual/transitional
- LP delegated reporting
- APA (MiFID) real-time publication

---

## 2) Core control principle

The reconciliation framework validates independent states:

- **Expected** (golden source reporting baseline)
- **Submitted** (vendor/submission channel payload)
- **Actual** (regulator/TR/APA feedback)

For LP delegated reporting, a two-stage control is modeled:

1. Internal vs LP alignment (stage 1)
2. LP submitted vs TR actual (stage 2)

---

## 3) Source systems and platforms

Primary source and transformation systems:

- Synapse DWH (`SYNAPSE-DWH-PROD`, `sql_dp_prod_we`)
- SQL Server RegReportDB (`AZR-WE-BI-21`)
- Hedge execution SQL (`AZR-W-REAL-DB-2-BIDBUser`, `etoro.Hedge.ExecutionLog`)
- Databricks (`main.general`, `main.regtech_stg`, `main.regtech`, `main.dealing`)
- External submission/feedback channels:
  - Cappitech (TR/ARM model submission)
  - S3 (CAT submission exchange)
  - TradeEcho / LSEG (APA)
  - DTCC (SFTR direct)
  - CME/CFTC via FIPS VM (LTR)

---

## 4) Direct reporting clarification (MiFID/EMIR/ASIC)

Operational/BI source layers are represented as **completeness comparison controls** and not as direct report-table generation inputs.

In diagrams, this is explicitly shown in MiFID/EMIR/ASIC model flows.

---

## 5) APA completeness control (newly added)

For APA model completeness checks, the baseline includes filtered comparisons against:

- `RegReportDB_Prod:MiFID.MIFID2_Report`
- `RegReportDB_Prod:MiFID.MIFID2_Hedge_Report`

This is now reflected in the APA model diagram.

---

## 6) Ingestion/coverage notes

Current coverage and constraints represented in diagrams:

- REGIS and TradeEcho response ingestion shown as active/live
- DTCC/TRAX/UNAVISTA coverage shown as partial/pending depending on flow
- LTR actual-state remains limited (acknowledgement/transfer tracking model)

---

## 7) Diagram index

### 7.1 Cross-model views

- Business flow by regulation:
  - `regtech-automation-project/diagrams/regtech-recon-business-architecture.md`
- Executive summary:
  - `regtech-automation-project/diagrams/regtech-recon-engine-exec-diagram.md`
- Detailed engineering:
  - `regtech-automation-project/diagrams/regtech-architecture-diagram.md`
- XML-converted technical view:
  - `regtech-automation-project/diagrams/trade-recon-architecture-v2-from-xml.md`
  - draw.io XML: `regtech-automation-project/diagrams/trade-recon-architecture-v2-from-mermaid.xml`

### 7.2 Per-reporting-model data-source diagrams

- Index: `regtech-automation-project/diagrams/reporting-model-data-source-flows.md`
- MiFID: `regtech-automation-project/diagrams/reporting-model-mifid-data-sources.md`
- EMIR: `regtech-automation-project/diagrams/reporting-model-emir-data-sources.md`
- ASIC: `regtech-automation-project/diagrams/reporting-model-asic-data-sources.md`
- CAT: `regtech-automation-project/diagrams/reporting-model-cat-data-sources.md`
- SFTR: `regtech-automation-project/diagrams/reporting-model-sftr-data-sources.md`
- LTR: `regtech-automation-project/diagrams/reporting-model-ltr-data-sources.md`
- LP delegated: `regtech-automation-project/diagrams/reporting-model-lp-delegated-data-sources.md`
- APA: `regtech-automation-project/diagrams/reporting-model-apa-data-sources.md`

