# Trade Reporting Reconciliation Automation - Workstream Index

Last updated: 2026-03-18

This page tracks repository artifacts by project phase and Jira workstream.

## 1) Phase plan (from REG-3279)

| Phase | Net days | Notes | Repository artifact |
|---|---:|---|---|
| Regulatory regime mapping + scope definition | 0.25 | Already owned knowledge | `Trade_Reporting_Reconciliation_Phase1_Scope_Definition.md` |
| Data source inventory + field mapping matrix | 2-3 | Heaviest lift | `Trade_Reporting_Reconciliation_Data_Source_Inventory_Catalog.md` + `Trade_Reporting_Reconciliation_Field_Mapping_Matrix.md` |
| Data quality assessment | 1-1.5 | Document known gaps | Section in inventory catalog + architecture doc |
| Tool/tech evaluation | 0.5-1 | Mostly documenting existing stack | `Trade_Reporting_Reconciliation_Architecture_Updated.md` |
| Architecture + flow diagram design | 2-3 | Core deliverable, iterative | `../diagrams/*` |
| Exception handling design | 0.5-1 | Templated from ops practice | Architecture remediation sections |
| Design documentation + packaging | 1 | Stakeholder-ready pack | This folder + root README links |

## 2) Scope and requirements artifacts (Epic REG-3283)

- Phase 1 scope definition:
  - `Trade_Reporting_Reconciliation_Phase1_Scope_Definition.md`
- Phase 1 reconciliation objectives and success criteria:
  - `Trade_Reporting_Reconciliation_Phase1_Objectives_and_Success_Criteria.md`
- Technical and architecture consolidation:
  - `Trade_Reporting_Reconciliation_Architecture_Updated.md`

## 3) Data inventory artifacts (Step 2)

- Master source inventory:
  - `Trade_Reporting_Reconciliation_Data_Source_Inventory_Catalog.md`
- Field-level reconciliation mapping matrix:
  - `Trade_Reporting_Reconciliation_Field_Mapping_Matrix.md`
- Jira story decomposition for Step 2 execution:
  - `Trade_Reporting_Reconciliation_Step2_Jira_Story_Breakdown.md`
- Manager-ready one-page status summary:
  - `Trade_Reporting_Reconciliation_Manager_Update_One_Pager.md`
- Per-reporting-model diagrams:
  - `../diagrams/reporting-model-data-source-flows.md`

## 4) Corrections applied vs initial draft notes

1. **MiFID vs EMIR/ASIC submission taxonomy**
   - MiFID EU/UK is ARM-based (TRAX path).
   - EMIR EU/UK and ASIC are TR-based (REGIS/DTCC paths by flow).

2. **LTR classification**
   - LTR should be modeled as a position/account-ownership and threshold regime (EOD + 102A context), not a pure transaction-level regime.

3. **Vendor naming normalization**
   - `TradEcho` normalized to `TradeEcho`.

4. **Acceptance vs accuracy**
   - Regulatory acceptance is tracked as a distinct control dimension and does not, by itself, prove field-level economic accuracy.
