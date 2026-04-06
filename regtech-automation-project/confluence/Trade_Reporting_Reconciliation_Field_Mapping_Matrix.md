# Step 2B - Field-Level Reconciliation Mapping Matrix

Last updated: 2026-03-18  
Workstream: REG-3279 Step 2 (field mapping matrix)  
Owner: Valentinos Konstantinou

## 1) Purpose

This artifact defines field-level lineage and control logic across the reconciliation chain:

- **Source (internal truth)**
- **Reporting table/output (expected)**
- **Submission evidence (submitted)**
- **Response/acknowledgement evidence (actual)**

This is the deliverable your manager asked for when saying "map data sources by field."

## 2) Difference from the source inventory catalog

- `Trade_Reporting_Reconciliation_Data_Source_Inventory_Catalog.md` answers:
  - **Which systems/files/tables exist?**
- This matrix answers:
  - **How each regulatory field reconciles end-to-end?**

Both are needed; this matrix is the control-design artifact.

## 3) Global field-mapping template (canonical)

| Model | Regulation | Reporting object | Reporting field (expected) | Canonical meaning | Source system/table.field (expected origin) | Transform/enrichment rule | Submitted evidence field (vendor payload/file) | Actual evidence field (response/repository) | Reconciliation key(s) | Match rule / tolerance | Timeliness rule | Severity if failed | Owner | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MiFID | MiFID II EU/UK | Trade | `MIFID2_Report.Notional` | Trade notional in reporting currency | `...` | `...` | `Cappitech payload notional` | `TRAX response notional/ack` | UTI + TradeID | Exact or product-tolerance | T+1 | Critical/Warning | Ops + Data | Draft | Example |

## 4) Wave 1 populated matrix (MiFID + EMIR critical fields)

This section is a concrete first delivery for manager review.  
It is designed as implementation-ready content with explicit "SME validation required" status where physical column names may differ by feed version.

### 4.1 MiFID (EU/UK, ARM-based via TRAX)

| Model | Regulation | Reporting object | Reporting field (expected) | Source system/table.field (expected origin) | Submitted evidence field | Actual evidence field | Reconciliation key(s) | Match rule / tolerance | Timeliness | Severity | Owner | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MiFID | MiFID II EU/UK | Trade | `MIFID2_Report.UTI` | Trading/Reg staging UTI lineage -> `MIFID2_ext_*` | Cappitech MiFID payload UTI | TRAX ARM response UTI/ack reference | UTI | Exact match | T+1 | Critical | Reg Ops + Data Eng | Ready for SME validation | Primary identity field |
| MiFID | MiFID II EU/UK | Trade | `MIFID2_Report.TransactionReferenceNumber` | RegReportDB MiFID source record ID | Cappitech transaction reference | TRAX transaction reference echo | UTI + transaction reference | Exact match | T+1 | Critical | Reg Ops | Ready for SME validation | Distinct from UTI in some flows |
| MiFID | MiFID II EU/UK | Trade | `MIFID2_Report.ExecutionTimestamp` | Trading execution timestamp (`Hedge.ExecutionLog` / trade source) | Payload execution datetime | TRAX accepted execution datetime | UTI | Exact (UTC normalization) | T+1 | Critical | Trading Tech + Reg Ops | Ready for SME validation | Timezone normalization required |
| MiFID | MiFID II EU/UK | Trade | `MIFID2_Report.BuyerLEI` | Customer/legal entity mapping (`MIFID2_Customer` / ext) | Payload buyer LEI | TRAX validation/ack buyer LEI | UTI + side | Exact regex + value match | T+1 | Critical | Compliance Data + Reg Ops | Ready for SME validation | LEI format check (20 chars) |
| MiFID | MiFID II EU/UK | Trade | `MIFID2_Report.SellerLEI` | Customer/legal entity mapping (`MIFID2_Customer` / ext) | Payload seller LEI | TRAX validation/ack seller LEI | UTI + side | Exact regex + value match | T+1 | Critical | Compliance Data + Reg Ops | Ready for SME validation | LEI format check (20 chars) |
| MiFID | MiFID II EU/UK | Trade | `MIFID2_Report.InstrumentID` | Instrument reference (`FIRDS_*`, `MIFID2_*`) | Payload ISIN/instrument ID | TRAX instrument acceptance field | UTI + instrument | Exact match | T+1 | Critical | Reg Data Management | Ready for SME validation | FIRDS alignment dependency |
| MiFID | MiFID II EU/UK | Trade | `MIFID2_Report.Notional` | Trade economics source -> `MIFID2_ext_*` | Payload notional amount | TRAX amount echo/validation | UTI + instrument + currency | Numeric tolerance class N1 (0 for fixed income; configurable for FX) | T+1 | Warning/Critical | Reg Ops + Finance Control | Draft rule - calibrate | Product-specific thresholds |
| MiFID | MiFID II EU/UK | Trade | `MIFID2_Report.Price` | Internal execution price source | Payload price | TRAX price validation/echo | UTI + instrument | Numeric tolerance class P1 (tick/precision rule) | T+1 | Warning/Critical | Reg Ops + Trading Tech | Draft rule - calibrate | Tick-size aware |
| MiFID | MiFID II EU/UK | Trade | `MIFID2_Report.Quantity` | Internal quantity from trade source | Payload quantity | TRAX quantity echo/validation | UTI + instrument | Numeric tolerance class Q1 (normally exact) | T+1 | Warning | Reg Ops | Ready for SME validation | Decimal precision standardization |
| MiFID | MiFID II EU/UK | Trade | `MIFID2_Report.Currency` | Trade currency source | Payload currency | TRAX currency check | UTI | Exact ISO-4217 | T+1 | Critical | Reg Ops | Ready for SME validation | Enforce uppercase ISO code |
| MiFID | MiFID II EU/UK | Trade | `MIFID2_Report.BuySellIndicator` | Internal side flag | Payload side | TRAX side validation | UTI | Exact enum mapping (`BUY/SELL`) | T+1 | Critical | Reg Ops | Ready for SME validation | Side-code conversion table |
| MiFID | MiFID II EU/UK | Trade | `MIFID2_Report.TradingVenue` | Venue mapping (`MIFID2_*`, reference data) | Payload venue MIC | TRAX venue validation | UTI + instrument | Exact MIC code match | T+1 | Warning | Reg Ops + Reference Data | Ready for SME validation | Venue whitelist required |

### 4.2 EMIR (EU/UK, TR-based via Regis-TR/DTCC)

| Model | Regulation | Reporting object | Reporting field (expected) | Source system/table.field (expected origin) | Submitted evidence field | Actual evidence field | Reconciliation key(s) | Match rule / tolerance | Timeliness | Severity | Owner | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EMIR | EMIR EU/UK | Trade/Lifecycle | `EMIR2_Refit_Report.UTI` | EMIR source + ext lineage (`EMIR2_*`, `EMIR2_ext_*`) | Cappitech TR payload UTI | REGIS/DTCC response UTI | UTI | Exact match | T+1 | Critical | Reg Ops + Data Eng | Ready for SME validation | Primary EMIR key |
| EMIR | EMIR EU/UK | Trade/Lifecycle | `EMIR2_Refit_Report.ActionType` | Internal lifecycle event classification | Payload event/action type | TR response action/status | UTI + event timestamp | Exact enum with transition matrix | T+1 | Critical | Reg Ops | Ready for SME validation | NEW/MODI/TERM rules |
| EMIR | EMIR EU/UK | Trade/Lifecycle | `EMIR2_Refit_Report.EventDate` | Internal lifecycle event date | Payload event date | TR accepted event date | UTI + action | Exact date (UTC/day normalization) | T+1 | Critical | Reg Ops | Ready for SME validation | Date normalization rule |
| EMIR | EMIR EU/UK | Trade | `EMIR2_Refit_Report.Counterparty1LEI` | Counterparty mapping (`EMIR2_Customer`, refs) | Payload CP1 LEI | TR validation for CP1 LEI | UTI | Exact regex + value match | T+1 | Critical | Compliance Data + Reg Ops | Ready for SME validation | LEI format control |
| EMIR | EMIR EU/UK | Trade | `EMIR2_Refit_Report.Counterparty2LEI` | Counterparty mapping (`EMIR2_Customer`, refs) | Payload CP2 LEI | TR validation for CP2 LEI | UTI | Exact regex + value match | T+1 | Critical | Compliance Data + Reg Ops | Ready for SME validation | LEI format control |
| EMIR | EMIR EU/UK | Trade | `EMIR2_Refit_Report.NotionalAmount` | Internal economics source | Payload notional amount | TR amount validation/echo | UTI + currency | Numeric tolerance class N1 | T+1 | Warning/Critical | Reg Ops + Finance Control | Draft rule - calibrate | Product-specific tolerance |
| EMIR | EMIR EU/UK | Trade | `EMIR2_Refit_Report.NotionalCurrency` | Internal currency source | Payload currency | TR currency validation | UTI | Exact ISO-4217 | T+1 | Critical | Reg Ops | Ready for SME validation | ISO enforcement |
| EMIR | EMIR EU/UK | Trade | `EMIR2_Refit_Report.Price` | Internal trade economics source | Payload price/rate | TR price/rate validation | UTI + product | Numeric tolerance class P1 | T+1 | Warning | Reg Ops + Trading Tech | Draft rule - calibrate | Product-dependent |
| EMIR | EMIR EU/UK | Trade | `EMIR2_Refit_Report.UPI` | Reference enrichment (`UPI_*`, RTS refs) | Payload UPI | TR UPI validation/status | UTI + product | Exact match | T+1 | Critical | Reg Data Management | Ready for SME validation | UPI source quality dependency |
| EMIR | EMIR EU/UK | Trade | `EMIR2_Refit_Report.ProductClassification` | Instrument meta + reference mapping | Payload product class | TR product-class validation | UTI + UPI | Exact/allowed mapping set | T+1 | Warning | Reg Data Management | Ready for SME validation | Controlled mapping table |
| EMIR | EMIR EU/UK | Valuation | `EMIR2_Report_Refit_Collateral.ValuationAmount` | Internal valuation source | Payload valuation amount | TR valuation response field | UTI + valuation date | Numeric tolerance class V1 | T+1 | Warning | Reg Ops + Finance Control | Draft rule - calibrate | End-of-day valuation timing |
| EMIR | EMIR EU/UK | Collateral | `EMIR2_Report_Refit_Collateral.CollateralAmount` | Internal collateral source | Payload collateral amount | TR collateral response field | UTI + collateral set + date | Numeric tolerance class C1 | T+1 | Warning | Reg Ops + Collateral Ops | Draft rule - calibrate | Collateral rounding policy |

## 4.3 Wave 1 delivery status summary

| Model | Target rows | Populated rows | Status | Next action |
|---|---:|---:|---|---|
| MiFID | 12 | 12 | Populated (validation pending) | Confirm physical payload/response column names with Cappitech/TRAX team |
| EMIR | 12 | 12 | Populated (validation pending) | Confirm REGIS/DTCC response code mapping and nullable behaviors |
| Total Wave 1 | 24 | 24 | Populated | Move to response-code matrix and rule calibration |

## 5) Model-by-model worksheet sections

Use these sections to expand rows in batches:

### 5.1 MiFID (ARM-based)
- Priority fields:
  - UTI, LEI, ISIN/instrument, notional, price, quantity, side, execution timestamp, transaction reference.
- Evidence path:
  - Expected: `MIFID2_*` report outputs
  - Submitted: Cappitech -> TRAX payload fields
  - Actual: TRAX ARM response/ack fields

### 5.2 EMIR (TR-based)
- Priority fields:
  - UTI, action type, valuation amount, collateral amount, counterparty LEI, product identifiers.
- Evidence path:
  - Expected: `EMIR2_*` outputs
  - Submitted: Cappitech TR payload fields
  - Actual: REGIS/DTCC response fields

### 5.3 ASIC (TR-based)
- Priority fields:
  - transaction ID/UTI equivalents, lifecycle/action, valuation/collateral fields, product class.
- Evidence path:
  - Expected: `ASIC2_*` outputs
  - Submitted: Cappitech payload fields
  - Actual: DTCC/TR response fields

### 5.4 CAT (event-based)
- Priority fields:
  - order ID, event type, route/execution references, timestamps.

### 5.5 SFTR
- Priority fields:
  - lifecycle action, valuation, collateral, counterparty, instrument.

### 5.6 LTR
- Priority fields:
  - account owner, reportable status, position quantity, threshold indicators.

### 5.7 LP delegated
- Priority fields:
  - LP identifier, trade identifier, position/equity values, response status.

### 5.8 APA
- Priority fields:
  - publication ID/reference, timestamp, instrument, notional/price.

## 6) Completion definition for Step 2B

Step 2B is considered complete when:

1. Each in-scope model has a populated field matrix for critical fields.
2. Every mapped field has:
   - expected-source lineage,
   - submitted evidence mapping,
   - actual evidence mapping.
3. Match rule, tolerance, timeliness rule, and severity are defined.
4. Owners are assigned and sign-off status is recorded.

## 7) Suggested delivery order (to reduce risk)

1. MiFID + EMIR critical fields first (highest control visibility).
2. ASIC + SFTR next (lifecycle-heavy models).
3. CAT + APA + LTR + LP delegated after core template is stable.
