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

## 4) Wave 1, Wave 2, and Wave 3 populated matrix (all in-scope models)

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
| EMIR | EMIR EU/UK REFIT | Trade/Lifecycle | `EMIR2_Refit_Report_Daily.UTI` / `EMIR3_UK_Refit_Report_Daily.UTI` / `EMIR2_ETORO_Refit_Positions.UTI` / `EMIR2_ETORO_Refit_Trades.UTI` | Derived in SPs from `#all` + prior-day refs (`EMIR2_Refit_Report` / `EMIR3_UK_Refit_Report`) and deterministic ETORO patterns in positions/trades SPs | Cappitech TR payload UTI | REGIS/DTCC response UTI | UTI | Exact match | T+1 | Critical | Reg Ops + Data Eng | Procedure-validated (EU+UK+ETORO positions+trades) | EU/UK reuse prior-day UTI; ETORO flows use fixed AUSHN/AUSHP generation patterns |
| EMIR | EMIR EU/UK REFIT | Trade/Lifecycle | `EMIR2_Refit_Report_Daily.Ticket`, `Report_tracking_number`; `EMIR2_ETORO_Refit_Positions.Ticket`; `EMIR2_ETORO_Refit_Trades.Ticket` | Built in EU SP from `#all` with fallback to previous-day `ERP.Ticket`; ETORO positions/trades use deterministic ticket patterns (`AUSHN`/`AUSHP`) | Payload ticket/tracking refs | TR response reference IDs | UTI + ticket/tracking ref | Exact match | T+1 | Critical | Reg Ops | Procedure-validated (EU+ETORO positions+trades) | Key for continuity and audit traceability across all EMIR flows |
| EMIR | EMIR EU/UK REFIT | Trade/Lifecycle | `EMIR2_Refit_Report_Daily.Action_type` / `EMIR3_UK_Refit_Report_Daily.Action_type` | SP logic from `#all.Trade`, `OpenORClose`, and lifecycle state | Payload action type | TR action/status | UTI + event date | Exact enum with transition matrix | T+1 | Critical | Reg Ops | Procedure-validated (EU+UK) | Position rows generate `PSTN`; trade rows generate `TCTN`/`POSC` logic |
| EMIR | EMIR EU/UK REFIT | Lifecycle | `EMIR2_Refit_Report_Daily.Execution_timestamp` / `EMIR3_UK_Refit_Report_Daily.Execution_timestamp` | Prior-day fallback (`ERP.Execution_timestamp`) or current event from `#all.Occurred` | Payload execution timestamp | TR accepted execution timestamp | UTI + action | Exact timestamp (UTC normalization) | T+1 | Critical | Reg Ops | Procedure-validated (EU+UK) | Fallback strategy preserved in both procedures |
| EMIR | EMIR EU/UK REFIT | Lifecycle | `EMIR2_Refit_Report_Daily.Confirmation_timestamp` / `EMIR3_UK_Refit_Report_Daily.Confirmation_timestamp` | Prior-day fallback (`ERP.Confirmation_timestamp`) else event timestamp from `#all` | Payload confirmation timestamp | TR confirmation/validation timestamp | UTI | Exact timestamp (UTC normalization) | T+1 | Critical | Reg Ops | Procedure-validated (EU+UK) | Explicit fallback implemented in both flows |
| EMIR | EMIR EU/UK REFIT | Counterparty | `EMIR2_Refit_Report_Daily.Counterparty_2`, `Counterparty_2_identifier_type`; `EMIR3_UK_Refit_Report_Daily.Counterparty_2` | Derived via `EMIR2_Customer`, corporate details (`#emir_corporate_clients_details` / `#emir_UK_clients_details`), account-type/LEI logic | Payload CP2 fields | TR counterparty validation | UTI + counterparty | Exact regex + value mapping | T+1 | Critical | Compliance Data + Reg Ops | Procedure-validated (EU+UK) | Includes CID-specific overrides and entity fallback logic |
| EMIR | EMIR EU/UK REFIT | Counterparty obligation | `EMIR2_Refit_Report_Daily.Reporting_obligation_of_counterparty_2`; UK counterparty nature/threshold fields | EU SP branch logic by country-of-legislation (`GB` vs non-GB), REFIT flags, and account type; UK SP logic from client detail flags | Payload obligation/nature fields | TR validation fields | UTI + counterparty | Exact enum mapping | T+1 | Critical | Compliance + Reg Ops | Procedure-validated (EU+UK) | EU SP includes explicit DSR-7233 logic for reporting obligation |
| EMIR | EMIR EU/UK REFIT | Trade taxonomy | `UPI`, `Isda_taxonomy`, `Anna_underlying_structure`, `Anna_reference_rate`, `Anna_underlying_index` (EU + ETORO flows) and `UPI` (UK) | Joined from Fivetran taxonomy/UPI tables by InstrumentID in EU daily and both ETORO procedures; UK SP directly maps UPI | Payload UPI/taxonomy fields | TR UPI/classification validation | UTI + InstrumentID | Exact match | T+1 | Critical | Reg Data Management | Procedure-validated (EU+UK+ETORO positions+trades) | ETORO positions and trades flows carry `Anna_*` taxonomy fields |
| EMIR | EMIR EU/UK REFIT | Product classification | `Product_classification`, `Base_product`, `Sub_product`, `Further_sub_product` | SP case logic by `InstrumentTypeID`, `SettlementTypeID`, and large InstrumentID mappings | Payload classification fields | TR product-class validation | UTI + InstrumentID | Exact/allowed mapping set | T+1 | Warning | Reg Data Management | Procedure-validated (EU+UK) | Includes DSR updates for commodity/gold/iron instruments |
| EMIR | EMIR EU/UK REFIT | Valuation/Notional | `EMIR2_Refit_Report_Daily.Valuation_amount`, `Price`, `Notional_amount_of_leg_1`; `EMIR3_UK_Refit_Report_Daily.Valuation_amount`; `EMIR2_ETORO_Refit_Positions.Valuation_amount`; `EMIR2_ETORO_Refit_Trades.Notional_amount_of_leg_1` | Built from `#all` + `#PricesEOD` for EU/UK; ETORO positions SP recalculates valuation from `#RE_AGG_ASIC_Positions`; ETORO trades SP populates notional and leaves valuation empty for TCTN rows | Payload valuation/notional/price | TR valuation and amount response fields | UTI + valuation date | Numeric tolerance classes V1/N1/P1 | T+1 | Warning/Critical | Reg Ops + Finance Control | Procedure-validated (EU+UK+ETORO positions+trades) | Includes ISO/GBX handling, ETORO position valuation formula, and ETORO trade notional derivation |
| EMIR | EMIR EU/UK REFIT | Collateral | `EMIR3_UK_Refit_Report_Collateral.Variation_margin_posted_by_counterparty_1_post_haircut`, `Excess_collateral_posted_by_counterparty_1`, `Collateral_portfolio_code` | Built in collateral SP from `#equity` (`EMIR2_ext_DWH_V_Liabilities`) + eligible IDs from `EMIR2_Position`/`EMIR2_Customer` and aggregation layer | Payload collateral fields | TR collateral response fields | Collateral portfolio code + report date | Numeric tolerance class C1 | T+1 | Warning/Critical | Reg Ops + Collateral Ops | Procedure-validated (UK collateral) | Includes `MARU` action and USD collateral amount outputs |
| EMIR | EMIR EU/UK REFIT | Collateralization flag | `EMIR2_Refit_Report_Daily.Uncollateralised` | Derived in EU SP final insert from `Level` and specific counterparty list logic | Payload collateralization indicator | TR/state validation field | UTI + counterparty + level | Exact enum mapping | T+1 | Warning | Reg Ops + Compliance | Procedure-validated (EU) | Logic distinguishes `TCTN` vs `PSTN` and selected counterparties |

### 4.3 ASIC (TR-based via DTCC)

| Model | Regulation | Reporting object | Reporting field (expected) | Source system/table.field (expected origin) | Submitted evidence field | Actual evidence field | Reconciliation key(s) | Match rule / tolerance | Timeliness | Severity | Owner | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ASIC | ASIC | Trade | `ASIC2_Transactions.TransactionID` | ASIC source/ext lineage (`ASIC2_*`, `ASIC2_ext_*`) | Cappitech ASIC payload transaction ID | DTCC/TR response transaction ID | TransactionID | Exact match | T+2 | Critical | Reg Ops + Data Eng | Ready for SME validation | Primary ASIC identity |
| ASIC | ASIC | Trade | `ASIC2_Transactions.UTI` | Internal UTI/transaction reference lineage | Payload UTI | DTCC/TR UTI | UTI | Exact match | T+2 | Critical | Reg Ops | Ready for SME validation | Jurisdiction-specific optionality by product |
| ASIC | ASIC | Trade | `ASIC2_Transactions.ActionType` | Lifecycle source classification | Payload action/event code | DTCC/TR action status | TransactionID + action date | Exact enum + transition matrix | T+2 | Critical | Reg Ops | Ready for SME validation | NEW/MODI/TERM/CORR handling |
| ASIC | ASIC | Trade | `ASIC2_Transactions.EventDate` | Internal lifecycle event date | Payload event date | DTCC/TR accepted event date | TransactionID + action | Exact date (UTC/day normalization) | T+2 | Critical | Reg Ops | Ready for SME validation | Timezone standardization required |
| ASIC | ASIC | Trade | `ASIC2_Transactions.Counterparty1LEI` | Counterparty mapping (`ASIC2_Customer*`) | Payload CP1 LEI | TR validation CP1 LEI | TransactionID | Exact regex + value match | T+2 | Critical | Compliance Data + Reg Ops | Ready for SME validation | LEI format control |
| ASIC | ASIC | Trade | `ASIC2_Transactions.Counterparty2LEI` | Counterparty mapping (`ASIC2_Customer*`) | Payload CP2 LEI | TR validation CP2 LEI | TransactionID | Exact regex + value match | T+2 | Critical | Compliance Data + Reg Ops | Ready for SME validation | LEI format control |
| ASIC | ASIC | Trade | `ASIC2_Transactions.NotionalAmount` | Internal economics source | Payload notional | DTCC/TR amount validation | TransactionID + currency | Numeric tolerance class N1 | T+2 | Warning/Critical | Reg Ops + Finance Control | Draft rule - calibrate | Product-specific tolerance |
| ASIC | ASIC | Trade | `ASIC2_Transactions.NotionalCurrency` | Internal currency source | Payload currency | DTCC/TR currency validation | TransactionID | Exact ISO-4217 | T+2 | Critical | Reg Ops | Ready for SME validation | ISO uppercase enforcement |
| ASIC | ASIC | Trade | `ASIC2_Transactions.Price` | Internal execution economics | Payload price | DTCC/TR price validation | TransactionID + product | Numeric tolerance class P1 | T+2 | Warning | Reg Ops + Trading Tech | Draft rule - calibrate | Tick/precision normalization |
| ASIC | ASIC | Position | `ASIC2_Positions_AGG.PositionQuantity` | Internal positions source (`ASIC2_Positions*`) | Submitted position quantity | DTCC/TR position quantity ack | Account + instrument + date | Numeric tolerance class Q1 | T+2 | Warning/Critical | Reg Ops + Position Control | Draft rule - calibrate | End-of-day position roll alignment |
| ASIC | ASIC | Valuation | `ASIC2_Positions_AGG.ValuationAmount` | Internal valuation source | Submitted valuation amount | DTCC/TR valuation amount | Account + instrument + date | Numeric tolerance class V1 | T+2 | Warning | Reg Ops + Finance Control | Draft rule - calibrate | Rounding policy required |
| ASIC | ASIC | Collateral | `ASIC2_Collateral.CollateralAmount` | Internal collateral source | Submitted collateral amount | DTCC/TR collateral response field | Counterparty + collateral set + date | Numeric tolerance class C1 | T+2 | Warning | Reg Ops + Collateral Ops | Draft rule - calibrate | Collateral eligibility mapping dependency |

### 4.4 SFTR (Direct DTCC)

| Model | Regulation | Reporting object | Reporting field (expected) | Source system/table.field (expected origin) | Submitted evidence field | Actual evidence field | Reconciliation key(s) | Match rule / tolerance | Timeliness | Severity | Owner | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SFTR | SFTR EU | Lifecycle | `SFTR_Report.UTI` | Vision-derived lifecycle output (`bronze_sftr_report`) | DTCC XML UTI | DTCC ack/reject UTI | UTI | Exact match | T+1 | Critical | Reg Ops + Data Eng | Ready for SME validation | Primary SFTR key |
| SFTR | SFTR EU | Lifecycle | `SFTR_Report.ActionType` | Derived lifecycle action (`NEWT/MODI/VALU/ETRM`) | DTCC XML action | DTCC response action/status | UTI + action date | Exact enum + sequencing | T+1 | Critical | Reg Ops | Ready for SME validation | Sequence integrity control |
| SFTR | SFTR EU | Lifecycle | `SFTR_Report.EventDate` | Lifecycle derivation date | DTCC XML event date | DTCC accepted event date | UTI + action | Exact date (UTC/day normalization) | T+1 | Critical | Reg Ops | Ready for SME validation | Calendar normalization |
| SFTR | SFTR EU | Trade | `SFTR_Report.Counterparty1LEI` | Counterparty source mapping | DTCC XML CP1 LEI | DTCC LEI validation field | UTI | Exact regex + value match | T+1 | Critical | Compliance Data + Reg Ops | Ready for SME validation | LEI quality dependency |
| SFTR | SFTR EU | Trade | `SFTR_Report.Counterparty2LEI` | Counterparty source mapping | DTCC XML CP2 LEI | DTCC LEI validation field | UTI | Exact regex + value match | T+1 | Critical | Compliance Data + Reg Ops | Ready for SME validation | LEI quality dependency |
| SFTR | SFTR EU | Trade | `SFTR_Report.ISIN` | Instrument source + reference enrichment | DTCC XML ISIN | DTCC instrument validation | UTI + instrument | Exact match | T+1 | Critical | Reg Data Management | Ready for SME validation | Instrument master dependency |
| SFTR | SFTR EU | Trade | `SFTR_Report.NotionalAmount` | Vision economics source | DTCC XML notional | DTCC amount validation/echo | UTI + currency | Numeric tolerance class N1 | T+1 | Warning/Critical | Reg Ops + Finance Control | Draft rule - calibrate | Product-specific tolerance |
| SFTR | SFTR EU | Trade | `SFTR_Report.NotionalCurrency` | Internal currency source | DTCC XML currency | DTCC currency validation | UTI | Exact ISO-4217 | T+1 | Critical | Reg Ops | Ready for SME validation | ISO enforcement |
| SFTR | SFTR EU | Valuation | `SFTR_Report.MarketValue` | Valuation derivation source | DTCC XML market value | DTCC valuation response field | UTI + valuation date | Numeric tolerance class V1 | T+1 | Warning | Reg Ops + Finance Control | Draft rule - calibrate | EOD valuation window |
| SFTR | SFTR EU | Collateral | `SFTR_Report.CollateralAmount` | Collateral derivation source | DTCC XML collateral amount | DTCC collateral response field | UTI + collateral set + date | Numeric tolerance class C1 | T+1 | Warning | Reg Ops + Collateral Ops | Draft rule - calibrate | Collateral policy dependency |
| SFTR | SFTR EU | Lifecycle | `SFTR_Report.ReuseIndicator` | Internal collateral reuse source | DTCC XML reuse indicator | DTCC reuse validation/status | UTI + collateral set | Exact enum mapping | T+1 | Warning | Reg Ops + Collateral Ops | Ready for SME validation | Enum normalization required |
| SFTR | SFTR EU | Position | `SFTR_Report.OutstandingQuantity` | Position snapshot source (`gold_vision*`) | DTCC XML outstanding quantity | DTCC quantity validation/echo | UTI + instrument + date | Numeric tolerance class Q1 | T+1 | Warning/Critical | Reg Ops + Position Control | Draft rule - calibrate | Snapshot-to-lifecycle consistency |

### 4.5 CAT (US, event-based via S3 to FINRA CAT)

| Model | Regulation | Reporting object | Reporting field (expected) | Source system/table.field (expected origin) | Submitted evidence field | Actual evidence field | Reconciliation key(s) | Match rule / tolerance | Timeliness | Severity | Owner | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CAT | CAT US | Event | `Reg_US_COrders.OrderID` | US order lifecycle source (`main.general`/`main.bi_db`) | S3-delivered CAT order ID | FINRA feedback order ID | OrderID | Exact match | T+1 | Critical | US Ops + Data Eng | Ready for SME validation | Primary CAT identity |
| CAT | CAT US | Event | `Reg_US_COrders.EventType` | Internal event classification (`MENO/MEOR/MEOA/MEOF/MENOS`) | Submitted CAT event type | FINRA event-type status | OrderID + event seq | Exact enum + sequence controls | T+1 | Critical | US Ops | Ready for SME validation | Sequence breaks are critical |
| CAT | CAT US | Event | `Reg_US_COrders.EventTimestamp` | Internal event timestamp | Submitted event timestamp | FINRA accepted event timestamp | OrderID + event type | Exact timestamp (UTC normalization) | T+1 | Critical | US Ops + Trading Tech | Ready for SME validation | Timezone normalization required |
| CAT | CAT US | Event | `Reg_US_COrders.Symbol` | Internal instrument source | Submitted symbol | FINRA symbol validation | OrderID + event seq | Exact symbol match | T+1 | Warning | US Ops | Ready for SME validation | Symbol normalization (suffix rules) |
| CAT | CAT US | Event | `Reg_US_COrders.Side` | Internal side indicator | Submitted side | FINRA side validation | OrderID + event seq | Exact enum mapping (`B/S`) | T+1 | Critical | US Ops | Ready for SME validation | Side-code translation table |
| CAT | CAT US | Event | `Reg_US_COrders.Quantity` | Internal order quantity | Submitted quantity | FINRA quantity validation | OrderID + event seq | Numeric tolerance class Q1 (normally exact) | T+1 | Warning | US Ops | Draft rule - calibrate | Amend/cancel quantity behavior |
| CAT | CAT US | Event | `Reg_US_COrders.Price` | Internal order price | Submitted price | FINRA price validation | OrderID + event seq | Numeric tolerance class P1 | T+1 | Warning | US Ops + Trading Tech | Draft rule - calibrate | Price precision/tick handling |
| CAT | CAT US | Event | `Reg_US_COrders.RouteDestination` | Internal routing destination | Submitted route destination | FINRA route validation | OrderID + event seq | Exact match against venue map | T+1 | Warning | US Ops + Reference Data | Ready for SME validation | Destination mapping dependency |
| CAT | CAT US | Event | `Reg_US_COrders.AccountID` | Internal account mapping | Submitted account ID | FINRA account validation status | OrderID + account | Exact + format control | T+1 | Critical | US Ops + Compliance | Ready for SME validation | PII masking policy must be respected |
| CAT | CAT US | Event | `Reg_US_COrders.ClientOrderID` | Internal client order reference | Submitted client order ID | FINRA client order reference | OrderID + client order ID | Exact match | T+1 | Warning | US Ops | Ready for SME validation | Join key for lifecycle stitching |
| CAT | CAT US | Event | `Reg_US_COrders.FirmROEID` | Internal reporting entity mapping | Submitted firm/ROE identifier | FINRA reporter validation | OrderID + reporter | Exact match | T+1 | Critical | US Ops + Compliance | Ready for SME validation | Regulatory party attribution |
| CAT | CAT US | Event | `Reg_US_COrders.FeedbackStatus` | Derived from CAT feedback ingest | Submitted event reference | FINRA feedback status code | OrderID + event seq | Status mapping matrix (accept/reject/corrected) | T+1 | Critical | US Ops | Ready for SME validation | Linked to rejection workflow |

### 4.6 APA (EU, real-time publication via TradeEcho)

| Model | Regulation | Reporting object | Reporting field (expected) | Source system/table.field (expected origin) | Submitted evidence field | Actual evidence field | Reconciliation key(s) | Match rule / tolerance | Timeliness | Severity | Owner | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| APA | APA EU | Publication event | `APA_Report.PublicationID` | Internal APA event key | APA Event Hub publication ID | TradeEcho confirmation publication ID | PublicationID | Exact match | Near real-time | Critical | Reg Ops + Data Eng | Ready for SME validation | Primary APA identity |
| APA | APA EU | Publication event | `APA_Report.TradeID` | Internal trade reference (`client_trade_evh`) | Submitted trade ID | TradeEcho trade ID/echo | TradeID | Exact match | Near real-time | Critical | Reg Ops | Ready for SME validation | Bridge to MiFID baseline |
| APA | APA EU | Publication event | `APA_Report.ExecutionTimestamp` | Internal execution timestamp | Submitted execution timestamp | TradeEcho execution timestamp echo | TradeID | Exact (UTC normalization) | Near real-time | Critical | Reg Ops + Trading Tech | Ready for SME validation | Event-time normalization |
| APA | APA EU | Publication event | `APA_Report.PublicationTimestamp` | Event Hub publish timestamp | Submitted publication timestamp | TradeEcho confirmation timestamp | PublicationID | Max delay threshold class T1 | Near real-time | Critical | Reg Ops | Draft rule - calibrate | Delay threshold approval needed |
| APA | APA EU | Publication event | `APA_Report.InstrumentID` | Instrument source/reference mapping | Submitted instrument ID | TradeEcho instrument validation | TradeID + instrument | Exact match | Near real-time | Critical | Reg Data Management | Ready for SME validation | Instrument master dependency |
| APA | APA EU | Publication event | `APA_Report.Price` | Internal trade economics source | Submitted price | TradeEcho price echo/validation | TradeID + instrument | Numeric tolerance class P1 | Near real-time | Warning | Reg Ops + Trading Tech | Draft rule - calibrate | Precision policy needed |
| APA | APA EU | Publication event | `APA_Report.Quantity` | Internal quantity source | Submitted quantity | TradeEcho quantity echo | TradeID + instrument | Numeric tolerance class Q1 | Near real-time | Warning | Reg Ops | Draft rule - calibrate | Quantity precision standard |
| APA | APA EU | Publication event | `APA_Report.Notional` | Internal notional derivation | Submitted notional | TradeEcho notional validation | TradeID + currency | Numeric tolerance class N1 | Near real-time | Warning/Critical | Reg Ops + Finance Control | Draft rule - calibrate | Product-specific thresholds |
| APA | APA EU | Publication event | `APA_Report.Currency` | Internal currency source | Submitted currency | TradeEcho currency validation | TradeID | Exact ISO-4217 | Near real-time | Critical | Reg Ops | Ready for SME validation | ISO uppercase enforcement |
| APA | APA EU | Publication event | `APA_Report.Venue` | Internal venue mapping | Submitted venue/MIC | TradeEcho venue validation | TradeID + venue | Exact MIC code | Near real-time | Warning | Reg Ops + Reference Data | Ready for SME validation | Venue whitelist dependency |
| APA | APA EU | Publication event | `APA_Report.DeferralFlag` | Internal deferral logic output | Submitted deferral indicator | TradeEcho deferral acceptance | PublicationID | Exact enum + eligibility checks | Near real-time | Critical | Compliance + Reg Ops | Ready for SME validation | Deferral policy dependency |
| APA | APA EU | Publication event | `APA_Report.ResponseStatus` | Derived from TradeEcho response ingest | Submitted publication reference | TradeEcho response status code | PublicationID | Status mapping matrix | Near real-time | Critical | Reg Ops | Ready for SME validation | Drives exception workflow |

### 4.7 LTR (US, EOD positions and 102A context via CME/CFTC)

| Model | Regulation | Reporting object | Reporting field (expected) | Source system/table.field (expected origin) | Submitted evidence field | Actual evidence field | Reconciliation key(s) | Match rule / tolerance | Timeliness | Severity | Owner | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LTR | LTR US | Position | `LTR_Report.AccountID` | Customer ownership source (`customer_radar_view_dim_customer`) | Submitted account identifier | CME/CFTC ack account reference | AccountID + date | Exact match | T+1 ops window | Critical | Ops + Compliance Reporting | Ready for SME validation | Core account key |
| LTR | LTR US | Position | `LTR_Report.BeneficialOwnerID` | Beneficial owner mapping source | Submitted owner identifier | Acknowledgement owner reference | AccountID + owner | Exact + format validation | T+1 ops window | Critical | Compliance | Ready for SME validation | 102A dependency |
| LTR | LTR US | Position | `LTR_Report.ReportingEntity` | Internal reporting-entity mapping | Submitted reporting entity | Ack reporting entity | AccountID + date | Exact match | T+1 ops window | Critical | Compliance + Ops | Ready for SME validation | Legal entity attribution |
| LTR | LTR US | Position | `LTR_Report.InstrumentSymbol` | Futures holdings source (`...eodholdings_futures`) | Submitted symbol | Ack symbol/reference | AccountID + symbol + date | Exact symbol match | T+1 ops window | Warning | Ops | Ready for SME validation | Symbol normalization rules |
| LTR | LTR US | Position | `LTR_Report.PositionDate` | EOD snapshot date | Submitted position date | Ack position date | AccountID + symbol | Exact date | T+1 ops window | Critical | Ops | Ready for SME validation | Business-day calendar alignment |
| LTR | LTR US | Position | `LTR_Report.PositionQuantity` | EOD holdings quantity | Submitted quantity | Ack/control total quantity | AccountID + symbol + date | Numeric tolerance class Q1 | T+1 ops window | Warning/Critical | Ops + Position Control | Draft rule - calibrate | Product-specific rounding |
| LTR | LTR US | Position | `LTR_Report.LongShortIndicator` | Internal position sign logic | Submitted long/short indicator | Ack validation code | AccountID + symbol + date | Exact enum mapping | T+1 ops window | Warning | Ops | Ready for SME validation | Direction mapping controls |
| LTR | LTR US | Control | `LTR_Report.ThresholdBreachFlag` | Threshold engine output (`bronze_ltr_cftc_thresholds`) | Submitted breach flag | Ack/control validation | AccountID + date | Exact boolean + threshold proof | T+1 ops window | Critical | Compliance + Ops | Ready for SME validation | Core regulatory criterion |
| LTR | LTR US | Control | `LTR_Report.ReportableFlag` | Internal reportable-determination logic | Submitted reportable indicator | Ack status/reportable class | AccountID + symbol + date | Exact rule outcome | T+1 ops window | Critical | Compliance | Ready for SME validation | Linked to threshold governance |
| LTR | LTR US | Owner data | `LTR_Report.Form102AReference` | 102A run outputs (`bronze_ltr_ocr_102a_runs`) | Submitted 102A reference | Transfer log + ack reference | AccountID + owner + date | Exact match | T+1 ops window | Critical | Compliance + Ops | Ready for SME validation | Personal-data controlled field |
| LTR | LTR US | Control total | `LTR_Report.FileControlTotal` | Derived from expected report population | Submitted control total | Transfer/ack control total | FileRunID + date | Exact/allowed variance class CT1 | T+1 ops window | Critical | Ops + Finance Control | Draft rule - calibrate | File-level completeness control |
| LTR | LTR US | Status | `LTR_Report.TransferStatus` | Derived from transfer logs (`bronze_ltr_transfers`) | Submission transfer reference | Ack/response status (`bronze_ltr_responses`) | FileRunID + transfer ID | Status mapping matrix | T+1 ops window | Critical | Ops | Ready for SME validation | No full TR-style lifecycle responses |

### 4.8 LP delegated (two-stage: internal vs LP, then LP vs TR)

| Model | Regulation | Reporting object | Reporting field (expected) | Source system/table.field (expected origin) | Submitted evidence field | Actual evidence field | Reconciliation key(s) | Match rule / tolerance | Timeliness | Severity | Owner | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LP delegated | EMIR/ASIC delegated flows | Trade | `LP_Recon.InternalTradeID` | Internal DUCO source (`v_dealing_duco_eodrecon`) | LP file trade ID reference | TR response trade reference | InternalTradeID + LPTradeID | Stage 1 exact link, Stage 2 reference match | T+1 | Critical | Dealing Ops + Reg Ops | Ready for SME validation | Core cross-system key |
| LP delegated | EMIR/ASIC delegated flows | Trade | `LP_Recon.LPTradeID` | LP staging tables (`LP_*`) | LP submitted trade ID | REGIS/UNAVISTA/DTCC response trade ID | LPTradeID | Exact match | T+1 | Critical | Dealing Ops | Ready for SME validation | LP-provided primary key |
| LP delegated | EMIR/ASIC delegated flows | Trade | `LP_Recon.UTI` | Internal + LP UTI lineage | LP submitted UTI | TR response UTI | UTI + LPTradeID | Exact match | T+1 | Critical | Reg Ops + Dealing Ops | Ready for SME validation | May be null in some LP flows |
| LP delegated | EMIR/ASIC delegated flows | Party | `LP_Recon.LPIdentifier` | LP source identifier mapping | Submitted LP identifier | TR reporter/counterparty identifier | LPIdentifier + date | Exact mapping set | T+1 | Warning | Dealing Ops | Ready for SME validation | Identifier normalization required |
| LP delegated | EMIR/ASIC delegated flows | Trade | `LP_Recon.InstrumentID` | Internal instrument + LP instrument mapping | LP submitted instrument | TR instrument validation | LPTradeID + instrument | Exact/allowed mapping | T+1 | Warning | Reg Data Management + Dealing Ops | Ready for SME validation | Cross-venue mapping table |
| LP delegated | EMIR/ASIC delegated flows | Trade | `LP_Recon.NotionalAmount` | Internal DUCO economics vs LP feed | LP submitted notional | TR response notional | LPTradeID + currency | Stage 1 tolerance N1, Stage 2 tolerance N1 | T+1 | Warning/Critical | Dealing Ops + Finance Control | Draft rule - calibrate | Two-stage tolerance application |
| LP delegated | EMIR/ASIC delegated flows | Trade | `LP_Recon.Quantity` | Internal DUCO quantity vs LP feed | LP submitted quantity | TR response quantity | LPTradeID + instrument + date | Stage 1 tolerance Q1, Stage 2 tolerance Q1 | T+1 | Warning/Critical | Dealing Ops + Position Control | Draft rule - calibrate | Position roll alignment |
| LP delegated | EMIR/ASIC delegated flows | Trade | `LP_Recon.Price` | Internal DUCO price vs LP feed | LP submitted price | TR response price | LPTradeID + instrument | Stage 1 tolerance P1, Stage 2 tolerance P1 | T+1 | Warning | Dealing Ops + Trading Tech | Draft rule - calibrate | Precision policy required |
| LP delegated | EMIR/ASIC delegated flows | Lifecycle | `LP_Recon.ActionType` | Internal lifecycle state vs LP action | LP submitted action | TR response action/status | LPTradeID + event date | Exact enum + transition matrix | T+1 | Critical | Reg Ops + Dealing Ops | Ready for SME validation | NEW/MODI/TERM sequencing |
| LP delegated | EMIR/ASIC delegated flows | Lifecycle | `LP_Recon.EventDate` | Internal event date vs LP event date | LP submitted event date | TR accepted event date | LPTradeID + action | Exact date (UTC/day normalization) | T+1 | Critical | Dealing Ops | Ready for SME validation | Date consistency across stages |
| LP delegated | EMIR/ASIC delegated flows | Submission | `LP_Recon.SubmissionReference` | LP submission log reference | LP file/control reference | TR ack submission reference | LPTradeID + submission ref | Exact match | T+1 | Critical | Reg Ops | Ready for SME validation | Required for auditability |
| LP delegated | EMIR/ASIC delegated flows | Status | `LP_Recon.ResponseStatus` | Derived from LP/TR ingestion | LP submitted reference | TR response status (REGIS/UNAVISTA/DTCC) | LPTradeID + submission ref | Status mapping matrix + aging rules | T+1 | Critical | Reg Ops | Ready for SME validation | Partial coverage for non-REGIS flows |

## 4.9 Wave 1, Wave 2, and Wave 3 delivery status summary

| Model | Target rows | Populated rows | Status | Next action |
|---|---:|---:|---|---|
| MiFID | 12 | 12 | Populated (validation pending) | Confirm physical payload/response column names with Cappitech/TRAX team |
| EMIR | 12 | 12 | Populated (EU+UK+ETORO positions+trades procedure-validated, endpoint validation pending) | Confirm REGIS/DTCC response code mapping and nullable behaviors; lock payload/response physical names |
| ASIC | 12 | 12 | Populated (validation pending) | Confirm DTCC response fields and lifecycle code set |
| SFTR | 12 | 12 | Populated (validation pending) | Confirm DTCC XML element mapping and ack schema version |
| CAT | 12 | 12 | Populated (validation pending) | Confirm FINRA feedback schema and event rejection classes |
| APA | 12 | 12 | Populated (validation pending) | Confirm TradeEcho response fields and latency threshold policy |
| LTR | 12 | 12 | Populated (validation pending) | Confirm CME/CFTC acknowledgement schema and 102A references |
| LP delegated | 12 | 12 | Populated (validation pending) | Confirm UNAVISTA/DTCC partial-ingestion handling rules |
| Total Wave 1 + Wave 2 + Wave 3 | 96 | 96 | Populated | Move to response-code matrix and tolerance calibration sign-off |

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

1. MiFID + EMIR critical fields first (highest control visibility). Completed in Wave 1.
2. ASIC + SFTR next (lifecycle-heavy models). Completed in Wave 2.
3. CAT + APA + LTR + LP delegated completed in Wave 3 (validation pending).
