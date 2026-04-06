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

## 4) Seeded mappings (initial examples)

These are starter rows to make implementation concrete. Replace placeholders with exact table/field names per squad validation.

| Model | Reporting field (expected) | Source field (internal) | Submitted evidence | Actual evidence | Key(s) | Match rule / tolerance | Timeliness | Severity | Status |
|---|---|---|---|---|---|---|---|---|---|
| MiFID | `MIFID2_Report.UTI` | Source UTI from trading/RegReport staging | UTI in Cappitech/TRAX submission | UTI in TRAX response | UTI | Exact match | T+1 | Critical | Draft |
| MiFID | `MIFID2_Report.Notional` | Internal notional field in source trade view | Notional in submitted payload | Notional or accepted echo value | UTI + instrument | Numeric tolerance by product | T+1 | Warning/Critical by variance | Draft |
| EMIR | `EMIR2_Refit_Report.EventType` | Internal lifecycle event type | Submitted lifecycle event | TR event acknowledgement/status | UTI + event timestamp | Allowed transition matrix | T+1 | Critical | Draft |
| EMIR | `EMIR2_Report_Refit_Collateral.CollateralValue` | Internal collateral source | Submitted collateral value | TR response/validation result | UTI + collateral set | Numeric tolerance | T+1 | Warning | Draft |
| ASIC | `ASIC2_Transactions.TransactionID` | Internal transaction ID | Submitted transaction ID | DTCC/TR response transaction ID | TransactionID | Exact match | T+2 | Critical | Draft |
| SFTR | SFTR lifecycle action field | Derived lifecycle event from Vision snapshots | DTCC XML submitted action | DTCC ack/reject action | UTI + action date | Exact + sequencing checks | T+1 | Critical | Draft |
| CAT | CAT event type (`MENO/MEOR/...`) | Internal order/event stream type | S3-delivered CAT event | FINRA feedback event status | OrderID + event seq | Exact sequence integrity | T+1 | Critical | Draft |
| APA | Publication timestamp field | Internal trade event timestamp | Event Hub publication timestamp | TradeEcho confirmation timestamp | TradeID | Max delay threshold | Near real-time | Critical | Draft |
| LTR | Position quantity in LTR payload | EOD holdings quantity source | CME/CFTC transfer payload quantity | Acknowledgement/control total evidence | Account + symbol + date | Tolerance by product/account | T+1 ops window | Warning/Critical | Draft |
| LP delegated | LP reconciliation quantity/value | Internal DUCO value and LP feed value | LP submitted record reference | TR response (REGIS/UNAVISTA/DTCC) | LP trade identifier + date | Stage 1 and Stage 2 separate tolerances | T+1 | Critical | Draft |

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
