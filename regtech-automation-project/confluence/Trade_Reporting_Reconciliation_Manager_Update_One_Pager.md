# Trade Reporting Reconciliation - Manager Update (One Pager)

Last updated: 2026-03-18  
Audience: Manager and project stakeholders

## 1) Executive summary

Step 2 has now been split and delivered in the intended sequence:

- **Step 2A (Catalog): completed**
  - Source register of systems/files/tables, ownership, frequency, storage, migration state.
- **Step 2B (Field mapping matrix): populated**
  - Field-level reconciliation mapping from **source -> expected reporting -> submitted evidence -> actual response evidence**.

This addresses the original gap between "data source inventory" and "field-by-field reconciliation mapping."

## 2) What is completed

### 2.1 Step 2A - Source inventory catalog

Artifact:
- `Trade_Reporting_Reconciliation_Data_Source_Inventory_Catalog.md`

Status:
- Completed and documented as a **catalog-only** artifact (not field mapping).
- Includes owners, formats, frequencies, storage locations, migration state, and sample references.

### 2.2 Step 2B - Field mapping matrix (critical fields)

Artifact:
- `Trade_Reporting_Reconciliation_Field_Mapping_Matrix.md`

Status:
- **96 populated rows** across all in-scope models:
  - MiFID: 12
  - EMIR: 12
  - ASIC: 12
  - SFTR: 12
  - CAT: 12
  - APA: 12
  - LTR: 12
  - LP delegated: 12

Each row captures:
- expected reporting field,
- source lineage,
- submitted evidence field,
- actual response field,
- reconciliation keys,
- tolerance/match class,
- timeliness rule,
- severity,
- owner,
- implementation status.

## 3) What remains (validation and sign-off)

Current state is "populated, validation pending." The following sign-offs are needed:

1. **Schema validation**
   - Confirm physical payload/response element names by endpoint/version.
2. **Response-code mapping lock**
   - Finalize accepted/rejected/corrected status classes per endpoint.
3. **Tolerance calibration**
   - Approve numeric tolerance classes (N1/P1/Q1/V1/C1) by product family.
4. **Ownership confirmation**
   - Confirm named accountable owners (not just role-level owners).

## 4) Risks and dependencies

- Endpoint schema versions may differ across flows (especially DTCC/UNAVISTA/CAT feedback variants).
- Non-uniform ingestion coverage still exists for selected response paths.
- LP delegated non-REGIS flows require explicit partial-coverage handling until ingestion closes.
- Tolerance calibration requires business/risk alignment to avoid false positives or missed breaches.

## 5) Recommended next step (immediate)

Run a **Step 2B validation workshop** (Ops + Compliance + Data Eng + model SMEs) to:

1. Validate sample fields per model (at least top 5 critical fields each),
2. Confirm response-code interpretation,
3. Approve first tolerance set for production-like pilot checks.

## 6) Proposed Jira update text (copy/paste)

```text
Progress update:
- Step 2A source inventory catalog is completed and documented (systems/files/tables + owner/frequency/storage/migration/sample refs).
- Step 2B field-level reconciliation matrix is now populated across all in-scope models.

Current coverage:
- 96 populated field mappings total:
  MiFID 12, EMIR 12, ASIC 12, SFTR 12, CAT 12, APA 12, LTR 12, LP delegated 12.

Each mapping row includes:
- source -> expected reporting -> submitted evidence -> actual response,
- keying strategy, tolerance class, timeliness rule, severity, owner, and status.

Next action requested:
- schedule validation/sign-off workshop to lock:
  1) payload/response physical field names,
  2) response status-code mapping,
  3) tolerance calibration by product class.
```

## 7) Reference artifacts

- Workstream index:
  - `Trade_Reporting_Reconciliation_Workstream_Index.md`
- Step 2A source register:
  - `Trade_Reporting_Reconciliation_Data_Source_Inventory_Catalog.md`
- Step 2A table-level appendix:
  - `Trade_Reporting_Reconciliation_Data_Source_Inventory_Table_Level_Appendix.md`
- Step 2B field-level matrix:
  - `Trade_Reporting_Reconciliation_Field_Mapping_Matrix.md`
- Step 2 Jira decomposition:
  - `Trade_Reporting_Reconciliation_Step2_Jira_Story_Breakdown.md`

## 8) New evidence ingested (procedure-level)

The following stored procedures have been ingested and used to tighten lineage/mapping:

- `dbo.SP_EMIR3_UK_Refit_Report_Daily`
- `dbo.SP_EMIR3_UK_Refit_Report_Collateral`
- `dbo.SP_EMIR2_Refit_Report_Daily`
- `dbo.SP_EMIR2_ETORO_Refit_Positions`

Impact:
- Step 2A now contains procedure-derived dependency lineage for:
  - EMIR UK REFIT daily report procedure
  - EMIR UK REFIT collateral report procedure
  - EMIR EU REFIT daily report procedure
  - EMIR ETORO positions report procedure
- Step 2B EMIR section now reflects procedure-validated field derivations for:
  - `UTI`
  - `Ticket` / `Report_tracking_number`
  - `Action_type`
  - `Execution_timestamp`
  - `Confirmation_timestamp`
  - counterparty fields
  - reporting-obligation logic fields
  - `UPI`
  - taxonomy fields (`Isda_taxonomy`, `Anna_*`)
  - product classification fields
  - valuation/notional/price fields
  - ETORO positions-specific Ticket/UTI derivation and valuation logic
  - `Uncollateralised`
  - collateral fields:
    - `Variation_margin_posted_by_counterparty_1_post_haircut`
    - `Excess_collateral_posted_by_counterparty_1`
    - `Collateral_portfolio_code`
