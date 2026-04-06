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
- `dbo.SP_EMIR2_ETORO_Refit_Trades`
- `dbo.SP_EMIR2_Seychelles_Refit_Report_Daily`
- `dbo.SP_EMIR3_ME_Refit_Report`
- `dbo.SP_EMIR2_Refit_Collateral`
- `dbo.SP_ASIC2_TransactionsReport`
- `dbo.SP_ASIC2_TransactionsReport_Hedge`
- `dbo.SP_ASIC2_PositionReport`
- `dbo.SP_ASIC2_PositionReport_Agg`
- `dbo.SP_ASIC2_PositionReport_Agg_Hedge`
- `dbo.SP_ASIC2_CollateralReport`
- `dbo.SP_MIFID2_Report`
- `dbo.SP_MIFID2_ETORO_Report`
- `dbo.SP_MIFID2_HedgeEU_Report`
- `dbo.SP_MIFID2_HedgeUK_Report`
- `dbo.SP_Reg_US_NOrders`
- `dbo.SP_Reg_US_Fullfilment`

Impact:
- Step 2A now contains procedure-derived dependency lineage for:
  - EMIR UK REFIT daily report procedure
  - EMIR UK REFIT collateral report procedure
  - EMIR EU REFIT daily report procedure
  - EMIR ETORO positions report procedure
  - EMIR ETORO trades report procedure
  - EMIR Seychelles REFIT daily report procedure
  - EMIR ME REFIT daily report procedure
  - EMIR EU REFIT collateral report procedure
  - ASIC transactions report procedure
  - ASIC hedge transactions report procedure
  - ASIC position report procedure
  - ASIC aggregated position report procedure
  - ASIC aggregated hedge position report procedure
  - ASIC collateral report procedure
  - MiFID report procedure (EU/UK + reg-change + Seychelles + ME branches)
  - CAT new-order procedure (current old model) with explicit transition note to fractional-native target model
  - CAT fulfillment procedure (current old model) with transition note for removal of inventory-fulfillment path
- Step 2B MiFID section now reflects procedure-validated field derivations for:
  - report routing (`RegulationReportID`: `1=EU`, `2=UK`)
  - occurred-under regulation lineage (`RegulationID` from `OrigRegulationID`)
  - deterministic transaction reference formatting (`TransactionReferenceNumber`)
  - migration controls (`RegChange=0/1/2` and migration-window logic)
  - buyer/seller identifier and decision-maker branch logic
  - split-adjusted quantity and GBX-normalized pricing
  - instrument classification and UK InstrumentID 341 ISIN override
  - execution timestamp/entity/venue branching across EU/UK inserts
  - short-selling indicator and asset-class population rules
  - EU AUS flow (`MIFID2_ETORO_Report`) transaction reference derivation
    (`PositionID + OpenORClose + 'AUS' + DateID`)
  - EU AUS fixed routing (`RegulationReportID=1`, `RegulationID=1`)
  - EU AUS side-driven buyer/seller LEI assignment and fixed LEI code types
  - EU AUS economics and timestamp sourcing from `ASIC_Transactions`
    (`OpenTime`, `OpenPrice`, `Volume`)
  - EU AUS commodity/price-type mapping from instrument currency type and
    instrument reference derivations (including 50-char name safeguard)
  - EU Hedge flow (`MIFID2_Hedge_Report`) routing controls
    (`RegulationReportID=1`, `rowSource=EU/EU-UK`)
  - EU Hedge deterministic transaction reference derivation from provider execution id,
    row ordering, and report date
  - EU Hedge counterparty/executing-entity LEI branching by side and LP profile
  - EU Hedge economics (`ExecutionTime`, `Units`, `ExecutionRate`) with GBX normalization
    and `numeric(16,8)` price casting
  - EU Hedge ED&F/IB enrichment for futures-related fields
    (`InstrumentFullName`, `NotionalCurrency1`, `PriceMultiplier`, `ExpiryDate`, `DeliveryType`)
  - EU Hedge controls including `ShortSellingIndicator`, `CommodityDerivativeIndicator`,
    `BackReportingIndicator=0`, and `EMSOrderID` propagation
  - UK Hedge flow (`MIFID2_Hedge_Report`) routing controls
    (`RegulationReportID=2`, `rowSource='UK'`)
  - UK Hedge deterministic transaction reference derivation from provider execution id,
    row ordering, and report date
  - UK Hedge counterparty/executing-entity LEI branching and FCA-specific scope
    (`IsMifidByFCA=1`)
  - UK Hedge economics (`ExecutionTime`, `Units`, `ExecutionRate`) with GBX normalization,
    `numeric(16,8)` price casting, and `TradingCapacity='MTCH'`
  - UK Hedge controls including `CommodityDerivativeIndicator`,
    `ExecutionWithinFirmType='ALG'`, `ExecutionWithinFirm='ETORODEALING01'`,
    `BackReportingIndicator=0`, and `EMSOrderID` propagation
- Step 2B CAT section now reflects procedure-validated and transition-aware controls for:
  - current `SP_Reg_US_NOrders` message construction (including ME-type branches `1/2/4/5`)
  - current `SP_Reg_US_Fullfilment` fulfillment construction (ME types `9/10` from NO lineage and EMS execution joins)
  - order identity/suffix logic (`ORDER_ID`, `SOURCE_ORDER_ID`, `CAT_ORDER_ID`, `_A`, `_RI`)
  - current fractional/roundup handling and representative linkage fields
  - symbol normalization via official FINRA symbol correction mapping
  - external/internal failure controls used for acceptance reconciliation
  - fulfillment-specific controls (`SOURCE_ORDER_ID`, `CAT_CLIENT_ORDER_ID`, `CAT_FIRM_ORDER_ID`, `ACTION_VOLUME`, `ACTION_PRICE`, `CORRECTION_DATETIME`)
  - announced target policy controls for cutover:
    - remove `ME_Type 2/3/4/10`,
    - keep `ME_Type 1/6/9`,
    - keep `ME_Type 5` only for copy-tree representative exact quantity
  - APCC.ETOR retirement control and 2026-03-26 test-file acceptance verification checkpoint
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
  - ETORO trades-specific Ticket/UTI derivation and notional (TCTN trade rows)
  - Seychelles-specific HN/HP Ticket/UTI patterns (RegulationID=9)
  - Seychelles direction backfill for zero-quantity rows (`for_update` strategy)
  - Seychelles valuation formula and valuation timestamp logic for `PSTN`
  - ME-specific MEHN/MEHP Ticket/UTI patterns (RegulationID=11)
  - ME direction backfill for zero-quantity rows (`for_update` strategy)
  - ME valuation formula and valuation timestamp logic for `PSTN`
  - EU collateral aggregation chain (`#collateral_ids` -> `#equity` -> `#collateral_calculation` -> `#collateral_calculation_agg*`)
  - EU collateral corporate/non-corporate split (`PRC1`/`PRC2`) and `MARU` action outputs
  - EU collateral exclusion controls (`regtech_excluded_*`, testing-CID list, historical open-date CID exclusion)
  - `Uncollateralised`
  - collateral fields:
    - `Variation_margin_posted_by_counterparty_1_post_haircut`
    - `Excess_collateral_posted_by_counterparty_1`
    - `Collateral_portfolio_code`
- Step 2B ASIC section now reflects procedure-validated field derivations for:
  - `UTI` deterministic pattern (`LEI + 'P' + PositionID + side + 'A'`)
  - counterparty and identifier type branch logic (`AccountTypeID`/`PlayerLevelID`/LEI overrides)
  - transaction lifecycle assembly from `#TRADE_OPEN`/`#HISTORY_OPEN`/`#HISTORY_CLOSE`/`#pop_in`
  - migration-driven reg-in/reg-out handling (`#ASIC2_RegOutDailyData`, `#RealEndPop`)
  - notional/price/quantity-unit derivation including GBX and non-ISO conversion handling
  - other-payment fields (`CDE_Other_payment_*`) from close-side `NetProfit` logic with payer/receiver backfill
  - hedge transformation logic from base ASIC transactions (`ASIC2_Transactions` -> `ASIC2_Transactions_Hedge`)
  - hedge UTI transform (`P` -> `H`), side inversion, and direction flip (`BYER`/`SLLR`)
  - hedge counterparty overrides (`CDE_Counterparty_2 = 213800GIFQMSV7HROS23`, identifier type `TRUE`, blank name/country)
  - position snapshot derivation from open-position state (`ASIC2_ext_OpenPositions_PositionsReport` -> `ASIC2_Positions`)
  - valuation close-price mapping from EOD bid/ask (`Reg_Ext_CurrencyPriceMaxDateWithSplit` with GBX normalization)
  - aggregate UTI lifecycle and switch-date logic in `ASIC2_Positions_AGG` (including excluded-UTI branch and targeted remediation cases)
  - aggregate SCD/open-close state management (`ASIC2_Positions_SCD` + history snapshot) and zero-quantity direction backfill
  - explicit aggregate valuation outputs (`CDE_Valuation_timestamp`, `CDE_Valuation_amount`, `CDE_Valuation_currency`, `CDE_Valuation_method`)
  - aggregate hedge UTI generation (`...HN...`) with incident-specific override mappings in `ASIC2_Positions_AGG_Hedge`
  - aggregate hedge net-direction and zero-quantity backfill logic (`for_update` -> prior-day non-zero direction)
  - aggregate hedge valuation recomputation from weighted buy/sell price legs and USD conversion
  - collateral population from `ASIC2_Positions_AGG` + liabilities source (`ASIC2_ext_DWH_V_Liabilities`) via `#ASIC2_collateral_calculation_agg`
  - collateral counterparty identifier branching and portfolio-code mapping (`Variation_margin_collateral_portfolio_code = CDE_Counterparty_2`)
  - collateral static output controls (`PRC2`, `TRUE` collateral indicator, `UTI` blank, end-of-day collateral timestamp)
