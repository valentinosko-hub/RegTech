# Step 2C Appendix - Regime-Level Completeness Logic (Tables, Keys, Filters)

Last updated: 2026-03-18  
Parent artifact: `Trade_Reporting_Reconciliation_Completeness_Control_Operational.md`  
Procedure reference: `dbo.usp_DailyCompleteness_Audit`

## 1) Purpose

This appendix provides the detailed implementation view for Step 2C by regime/flow:

- which tables are used,
- which filters are applied,
- which matching keys are used for mismatch detection,
- which cleanup/exclusion rules are applied before final completeness metrics.

## 2) Date window and shared setup used across all regimes

The procedure uses:

- `@Today = ISNULL(@AsOfDate, CAST(GETDATE() AS DATE))`
- `@ReportDate1 = CASE WHEN weekday(@Today)=Monday THEN @Today-3 ELSE @Today-1 END`
- `@ReportDate2 = @Today-1`
- `@ReportDate1ID/@ReportDate2ID` as `yyyymmdd` integer forms.

All regime sections below assume `ReportDate`/`Trade_date` filtering between `@ReportDate1` and `@ReportDate2` unless noted.

## 3) Shared exclusion and normalization controls

These controls are reused across multiple flows:

1. **Migration/reg-movement cleanup**
   - `dbo.Reg_Regulation_Movments_Positions`
   - `dbo.Reg_RegulationInOutDailyData`
   - Applied to remove expected timing-driven false mismatches around migration windows.

2. **Instrument eligibility filters**
   - `dbo.Reg_Instruments_SCD` with validity windows (`Trade_date >= ValidFrom` and `< ValidTo`)
   - Flags such as `IsMifid`, `IsMifidByFCA`.

3. **Customer exclusions for BI baseline**
   - `[ThirdParty_Fivetran].[Fivetran].[regtech].[regulation_report_excluded_cids]`.

4. **BI customer eligibility**
   - `Fact_SnapshotCustomer` filtered to:
     - `RegulationID IN (1,2,4,9,10,11)`
     - `PlayerLevelID <> 4`
     - `IsValidCustomer = 1`
     - `AccountTypeID NOT IN (7,9)`
     - `CountryID <> 250`.

### 3.1 Filter-to-table lineage map (table.column ownership)

Every filter used in Sections 4-6 is mapped below to its source table and column(s).

| Filter family | Filter expression (as used in procedure) | Source table.column(s) | Notes |
|---|---|---|---|
| Reporting date window | `ReportDate BETWEEN @ReportDate1 AND @ReportDate2` | `dbo.MIFID2_Report.ReportDate`, `dbo.MIFID2_ETORO_Report.ReportDate`, `dbo.MIFID2_ME_Report.ReportDate`, `dbo.MIFID2_Hedge_Report.ReportDate`, `dbo.EMIR2_Refit_Report.ReportDate`, `dbo.EMIR2_ETORO_Refit_Trades.ReportDate`, `dbo.EMIR3_ME_Refit_Report.ReportDate`, `dbo.ASIC2_Transactions.ReportDate` | Audit-side date filter family |
| BestEX date window | `Trade_date BETWEEN @ReportDate1 AND @ReportDate2` | `dbo.BestEX_Report.Trade_date` | Used in BestEX diagnostic joins (secondary) |
| MiFID report routing scope | `RegulationID`, `RegulationReportID`, `OpenORClose` filters | `dbo.MIFID2_Report.RegulationID`, `dbo.MIFID2_Report.RegulationReportID`, `dbo.MIFID2_Report.OpenORClose`, plus equivalent columns in `dbo.MIFID2_ETORO_Report` / `dbo.MIFID2_ME_Report` | Determines MiFID regime slices |
| BestEX entity/instrument scope | `eToroEntity`, `[CFD/Real]`, `OpenORClose` | `dbo.BestEX_Report.eToroEntity`, `dbo.BestEX_Report.[CFD/Real]`, `dbo.BestEX_Report.OpenORClose` | Counterpart filter family for MiFID/EMIR/ASIC |
| Instrument eligibility (internal) | `Trade_date >= ValidFrom AND Trade_date < ValidTo`, `IsMifid`, `IsMifidByFCA` | `dbo.Reg_Instruments_SCD.ValidFrom`, `dbo.Reg_Instruments_SCD.ValidTo`, `dbo.Reg_Instruments_SCD.IsMifid`, `dbo.Reg_Instruments_SCD.IsMifidByFCA` | Referenced from BestEX and BI enrichment logic |
| Migration position cleanup | `PrevRegulationID` / `RegulationID`, `OpenOccurred < Migration_Occurred` | `dbo.Reg_Regulation_Movments_Positions.PrevRegulationID`, `dbo.Reg_Regulation_Movments_Positions.RegulationID`, `dbo.Reg_Regulation_Movments_Positions.OpenOccurred`, `dbo.Reg_Regulation_Movments_Positions.Migration_Occurred` | Removes expected migration-timing differences |
| Migration transaction cleanup | `PrevRegulationID` / `RegulationID`, `ExecutionTime < Migration_Occurred` | `dbo.Reg_RegulationInOutDailyData.PrevRegulationID`, `dbo.Reg_RegulationInOutDailyData.RegulationID`, `dbo.Reg_RegulationInOutDailyData.ExecutionTime`, `dbo.Reg_RegulationInOutDailyData.Migration_Occurred` | Removes expected migration-timing differences |
| TraNa entity and product scope | `eToroEntity`, `OpenORClose`, `[CFD/Real]`, `InstrumentID` | `dbo.RegulationAggTrans.eToroEntity`, `dbo.RegulationAggTrans.OpenORClose`, `dbo.RegulationAggTrans.[CFD/Real]`, `dbo.RegulationAggTrans.InstrumentID` | Operational baseline count scope |
| TraNa MiFID eligibility flags | `IsMifidByESMA`, `IsMifidByFCA` | `dbo.RegulationAggTrans.IsMifidByESMA`, `dbo.RegulationAggTrans.IsMifidByFCA` | These flags are internal fields (not direct external API checks) |
| BI transaction/position population | open/close leg selection and active-position rules | `[SYNAPSE-DWH-PROD].[sql_dp_prod_we].[DWH_dbo].[Dim_Position].OpenDateID`, `.CloseDateID`, `.OriginalPositionID`, `.PositionID`, `.InstrumentID`, `.CID`, `.IsSettled`, `.OpenOccurred` | Used to construct BI trade/position populations |
| BI customer eligibility | regulation/player/account/country validity | `[SYNAPSE-DWH-PROD].[sql_dp_prod_we].[DWH_dbo].[Fact_SnapshotCustomer].RegulationID`, `.PlayerLevelID`, `.IsValidCustomer`, `.AccountTypeID`, `.CountryID`, `.DateRangeID`, `.RealCID` | Defines BI customer scope |
| BI date-range applicability | overlap between trade/position date and customer validity range | `[SYNAPSE-DWH-PROD].[sql_dp_prod_we].[DWH_dbo].[Dim_Range].FromDateID`, `.ToDateID`, `.DateRangeID` | Applies customer-range windows |
| BI CID exclusions | excluded customer IDs | `[ThirdParty_Fivetran].[Fivetran].[regtech].[regulation_report_excluded_cids].cid` | Removes known excluded CIDs from BI baseline |
| MiFID hedge BI quality filters | execution success and provider validity | `[AZR-W-REAL-DB-2-BIDBUser].[etoro].[Hedge].[ExecutionLog].Success`, `.ProviderExecID`, `.OrderState`, `.Units`, `.ExecutionTime`; `dbo.Reg_Ext_LiquidityAccountID.eToroEntity`; `dbo.Reg_LiquidtyAcount_SCD.ValidFrom/ValidTo`; `dbo.Reg_Instruments_SCD.IsMifid` | Hedge BI baseline specific |

### 3.2 Independence limitation (current state)

Important limitation for control interpretation:

- Instrument eligibility in completeness checks (`IsMifid`, `IsMifidByFCA`, date-valid instrument scope) is sourced from internal `dbo.Reg_Instruments_SCD` and internal downstream datasets that consume the same reference family.
- Reporting-table generation also relies on this same internal reference family.

Implication:

- Step 2C currently provides strong internal completeness reconciliation (Audit vs TraNa vs BI), but **does not yet provide independent external reference-data validation** for MiFID/FCA FIRDS eligibility.

### 3.3 Future enhancement - external reference-data validation

Planned enhancement is to add independent eligibility checks via external APIs:

- ESMA FIRDS:
  - `https://registers.esma.europa.eu/publication/searchRegister?core=esma_registers_firds#`
- FCA reference data:
  - `https://data.fca.org.uk/#/viewdata`

Target outcome:

- Validate internal eligibility flags (`IsMifid`, `IsMifidByFCA`) against independent external reference snapshots,
- Add a fourth control lens for reference-data independence (in addition to Audit vs TraNa vs BI completeness).

### 3.4 Regime comparison matrix (BI prioritized)

Completeness checks are interpreted in this order:

1. Primary: **Audit vs BI** (`Audit_vs_BI_Completeness`),
2. Secondary: **Audit vs TraNa** (`Audit_vs_TraNa_Completeness`),
3. Diagnostic: **BestEX set mismatches** where implemented.

| Regime | Primary comparison (used for completeness priority) | BI filter source tables and fields used for regime count | Secondary comparison | BestEX diagnostic |
|---|---|---|---|---|
| MiFID UK CL | Audit reporting tables vs BI baseline tables | `Fact_SnapshotCustomer.RegulationID IN (2)`; `Dim_Position.InstrumentID` / `Dim_Instrument.InstrumentTypeID` in MiFID scope; `Dim_Position.IsSettled`; `Reg_Instruments_SCD.IsMifidByFCA`; `regulation_report_excluded_cids.cid`; `Dim_Range.FromDateID/ToDateID` | Audit vs TraNa (`RegulationAggTrans`) | Yes (`MIFID2_Report` vs `BestEX_Report`) |
| MiFID EU CL | Audit reporting tables vs BI baseline tables | `Fact_SnapshotCustomer.RegulationID IN (1)`; `Dim_Position.InstrumentID` / `Dim_Instrument.InstrumentTypeID`; `Dim_Position.InstrumentID<>624`; `Dim_Position.IsSettled`; `Reg_Instruments_SCD.IsMifid`; `regulation_report_excluded_cids.cid`; `Dim_Range.FromDateID/ToDateID` | Audit vs TraNa (`RegulationAggTrans`) | Yes (`MIFID2_Report` vs `BestEX_Report`) |
| MiFID EU Hedge | Audit reporting tables vs BI hedge baseline | `Hedge.ExecutionLog.ExecutionTime/Success/Units/ProviderExecID/OrderState`; `Reg_Ext_LiquidityAccountID.eToroEntity`; `Reg_LiquidtyAcount_SCD.ValidFrom/ValidTo`; `Reg_Instruments_SCD.IsMifid` | Audit vs TraNa (`RegulationAggTrans`) | No |
| MiFID EU AUS | Audit reporting tables vs BI baseline tables | `Fact_SnapshotCustomer.RegulationID IN (4,10)`; `Dim_Position.InstrumentID` / `Dim_Instrument.InstrumentTypeID`; `Dim_Position.InstrumentID<>624`; `Dim_Position.IsSettled=0`; `Reg_Instruments_SCD.IsMifid`; `regulation_report_excluded_cids.cid`; `Dim_Range.FromDateID/ToDateID` | Audit vs TraNa (`RegulationAggTrans`) | Yes (`MIFID2_ETORO_Report` vs `BestEX_Report`) |
| MiFID EU SC | Audit reporting tables vs BI baseline tables | `Fact_SnapshotCustomer.RegulationID IN (9)`; `Dim_Position.InstrumentID` / `Dim_Instrument.InstrumentTypeID`; `Dim_Position.InstrumentID<>624`; `Dim_Position.IsSettled`; `Reg_Instruments_SCD.IsMifid`; `regulation_report_excluded_cids.cid`; `Dim_Range.FromDateID/ToDateID` | Audit vs TraNa (`RegulationAggTrans`) | Yes (`MIFID2_Report` vs `BestEX_Report`) |
| MiFID EU ME | Audit reporting tables vs BI baseline tables | `Fact_SnapshotCustomer.RegulationID IN (11)`; `Dim_Position.InstrumentID` / `Dim_Instrument.InstrumentTypeID`; `Dim_Position.InstrumentID<>624`; `Dim_Position.IsSettled`; `Reg_Instruments_SCD.IsMifid`; `regulation_report_excluded_cids.cid`; `Dim_Range.FromDateID/ToDateID` | Audit vs TraNa (`RegulationAggTrans`) | Yes (`MIFID2_ME_Report` vs `BestEX_Report`) |
| MiFID EU FCA | Audit reporting tables vs BI baseline tables | `Fact_SnapshotCustomer.RegulationID IN (2)`; `Dim_Position.InstrumentID` / `Dim_Instrument.InstrumentTypeID`; `Reg_Instruments_SCD.IsMifid=1`; `Reg_Instruments_SCD.IsMifidByFCA=1`; `Dim_Position.IsSettled`; `regulation_report_excluded_cids.cid`; `Dim_Range.FromDateID/ToDateID` | Audit vs TraNa (`RegulationAggTrans`) | Yes (`MIFID2_Report` vs `BestEX_Report`) |
| EMIR TR CL | Audit reporting tables vs BI baseline tables | `Fact_SnapshotCustomer.RegulationID IN (1,2)`; `Dim_Position` open-leg population (`OpenDateID` / `CloseDateID`); `Dim_Position.IsSettled=0`; `regulation_report_excluded_cids.cid`; `Dim_Range.FromDateID/ToDateID` | Audit vs TraNa (`RegulationAggTrans`) | Yes (`EMIR2_Refit_Report` vs `BestEX_Report`) |
| EMIR TR AUS | Audit reporting tables vs BI baseline tables | `Fact_SnapshotCustomer.RegulationID IN (4,10)`; `Dim_Position` open-leg population (`OpenDateID` / `CloseDateID`); `Dim_Position.IsSettled=0`; `regulation_report_excluded_cids.cid`; `Dim_Range.FromDateID/ToDateID` | Audit vs TraNa (`RegulationAggTrans`) | Yes (`EMIR2_ETORO_Refit_Trades` vs `BestEX_Report`) |
| EMIR TR SC | Audit reporting tables vs BI baseline tables | `Fact_SnapshotCustomer.RegulationID IN (9)`; `Dim_Position` open-leg population (`OpenDateID` / `CloseDateID`); `Dim_Position.IsSettled=0`; `regulation_report_excluded_cids.cid`; `Dim_Range.FromDateID/ToDateID` | Audit vs TraNa (`RegulationAggTrans`) | Yes (`EMIR2_Refit_Report` vs `BestEX_Report`) |
| EMIR TR ME | Audit reporting tables vs BI baseline tables | `Fact_SnapshotCustomer.RegulationID IN (11)`; `Dim_Position` open-leg population (`OpenDateID` / `CloseDateID`); `Dim_Position.IsSettled=0`; `regulation_report_excluded_cids.cid`; `Dim_Range.FromDateID/ToDateID` | Audit vs TraNa (`RegulationAggTrans`) | Yes (`EMIR3_ME_Refit_Report` vs `BestEX_Report`) |
| ASIC TR CL | Audit reporting tables vs BI baseline tables | `Fact_SnapshotCustomer.RegulationID IN (4,10)`; `Dim_Position` open+close leg population (`OpenDateID` / `CloseDateID`); `Dim_Position.IsSettled=0`; `regulation_report_excluded_cids.cid`; `Dim_Range.FromDateID/ToDateID` | Audit vs TraNa (`RegulationAggTrans`) | Yes (`ASIC2_Transactions` vs `BestEX_Report`) |
| ASIC TR EU | Audit reporting tables vs BI baseline tables | `Fact_SnapshotCustomer.RegulationID IN (4,10)`; `Dim_Position` open+close leg population (`OpenDateID` / `CloseDateID`); `Dim_Position.IsSettled=0`; `regulation_report_excluded_cids.cid`; `Dim_Range.FromDateID/ToDateID` | Audit vs TraNa (`RegulationAggTrans`) | Yes (`ASIC2_Transactions` vs `BestEX_Report`) |
| EMIR POS CL | Audit reporting tables vs BI baseline tables | `Fact_SnapshotCustomer.RegulationID IN (1,2)`; active-position logic in `Dim_Position` (`OpenDateID<=ReportDateID` and `CloseDateID=0 OR >ReportDateID`); `Dim_Position.OpenOccurred`; `Dim_Position.IsSettled=0`; `regulation_report_excluded_cids.cid`; `Dim_Range.FromDateID/ToDateID` | Not applicable | No |
| ASIC POS CL | Audit reporting tables vs BI baseline tables | `Fact_SnapshotCustomer.RegulationID IN (4,10)`; active-position logic in `Dim_Position` (`OpenDateID<=ReportDateID` and `CloseDateID=0 OR >ReportDateID`); `Dim_Position.IsSettled=0`; `regulation_report_excluded_cids.cid`; `Dim_Range.FromDateID/ToDateID` | Not applicable | No |

## 4) MiFID flows (7)

### 4.1 MiFID UK CL

- **Audit table**
  - `dbo.MIFID2_Report`
  - Filters: `RegulationID=2`, `RegulationReportID=2`, `OpenORClose IN ('C','O')`.
- **Mismatch counterpart**
  - `dbo.BestEX_Report`
  - Filters: `eToroEntity='eToro UK'`, `OpenORClose IN ('C','O')`, instrument in `Reg_Instruments_SCD` with `IsMifidByFCA=1`.
- **Join keys**
  - `CID`, `TransactionReferenceNumber=TradeID`, `InstrumentID`, `ReportDate=Trade_date`.
- **Cleanup filters**
  - Remove rows tied to migration windows for both audit-side and BestEX-side records using:
    - `Reg_Regulation_Movments_Positions` (`PrevRegulationID=2` or `RegulationID=2`)
    - `Reg_RegulationInOutDailyData` (`PrevRegulationID=2` or `RegulationID=2`).
- **TraNa baseline**
  - `dbo.RegulationAggTrans`
  - Filters: `eToroEntity='eToro UK'`, `OpenORClose IN ('ClientOpen','ClientClose')`, `IsMifidByFCA=1`, `IsMifidByESMA IN (0,1)`.
- **BI baseline (main tables)**
  - `[SYNAPSE-DWH-PROD].[sql_dp_prod_we].[DWH_dbo].[Dim_Position]`
  - `[SYNAPSE-DWH-PROD].[sql_dp_prod_we].[DWH_dbo].[Dim_Instrument]`
  - `[SYNAPSE-DWH-PROD].[sql_dp_prod_we].[DWH_dbo].[Fact_SnapshotCustomer]`
  - `[SYNAPSE-DWH-PROD].[sql_dp_prod_we].[DWH_dbo].[Dim_Range]`
  - `[ThirdParty_Fivetran].[Fivetran].[regtech].[regulation_report_excluded_cids]`
  - Filters: `RegulationID IN (2)`, instrument scope `(InstrumentID IN (319,341) OR InstrumentTypeID IN (4,5,6))`, `IsMifidByFCA=1`.

### 4.2 MiFID EU CL

- **Audit table**
  - `dbo.MIFID2_Report`
  - Filters: `RegulationID=1`, `RegulationReportID=1`, `OpenORClose IN ('C','O')`.
- **Mismatch counterpart**
  - `dbo.BestEX_Report` with `eToroEntity='eToro EU'`, MiFID-eligible instruments.
  - Missing-in-audit branch also excludes `InstrumentID=624`.
- **Join keys**
  - `CID`, `TransactionReferenceNumber=TradeID`, `InstrumentID`, `ReportDate=Trade_date`.
- **Cleanup filters**
  - Migration cleanup via `Reg_Regulation_Movments_Positions` and `Reg_RegulationInOutDailyData` with regulation `1`.
- **TraNa baseline**
  - `RegulationAggTrans` filters: `eToroEntity='eToro EU'`, `ClientOpen/ClientClose`, `IsMifidByESMA=1`, `IsMifidByFCA IN (0,1)`, `InstrumentID<>624`.
- **BI baseline (main tables)**
  - `Dim_Position`, `Dim_Instrument`, `Fact_SnapshotCustomer`, `Dim_Range`, `regulation_report_excluded_cids`.
  - Filters: `RegulationID IN (1)`, MiFID instrument scope, `InstrumentID<>624`, `IsMifid=1`.

### 4.3 MiFID EU Hedge

- **Audit table**
  - `dbo.MIFID2_Hedge_Report`
  - Filter: `RegulationReportID=1`.
- **Mismatch counterpart**
  - No BestEX temp mismatch table in current procedure.
  - Clean mismatch components are fixed to zero for this flow.
- **TraNa baseline**
  - `RegulationAggTrans` with `eToroEntity IN ('eToro EU','eToro UK')`, `OpenORClose='HedgeExecution'`, MiFID flags enabled, `InstrumentID<>624`.
- **BI baseline (main tables)**
  - `[AZR-W-REAL-DB-2-BIDBUser].[etoro].[Hedge].[ExecutionLog]`
  - `dbo.Reg_Ext_LiquidityAccountID`
  - `dbo.Reg_LiquidtyAcount_SCD`
  - `dbo.Reg_Instruments_SCD`
  - Core filters include successful executions, valid provider state, LP entity scope, and MiFID instrument eligibility.
- **Special rule**
  - If BI count equals Audit count, final completeness is forced to `1.0` and mismatch marked as false positive.

### 4.4 MiFID EU AUS

- **Audit table**
  - `dbo.MIFID2_ETORO_Report` with `RegulationID=1`, `RegulationReportID=1`, `OpenORClose IN ('C','O')`.
  - Transaction reference normalized with suffix trimming to match BestEX `TradeID`.
- **Mismatch counterpart**
  - `dbo.BestEX_Report` with `eToroEntity='eToro AUS'`, `[CFD/Real]='CFD'`, MiFID instrument eligibility.
  - Missing-in-audit branch excludes `InstrumentID=624`.
- **Join keys**
  - `CID`, normalized transaction reference to `TradeID`, `InstrumentID`, date.
- **Cleanup filters**
  - Synthetic trade suppression via `Reg_Regulation_Movments_Positions`.
  - Migration cleanup with `PrevRegulationID IN (4,10)` and `RegulationID IN (4,10)`.
- **TraNa baseline**
  - `RegulationAggTrans` with `eToroEntity='eToro AUS'`, `ClientOpen/ClientClose`, `[CFD/Real]='CFD'`, MiFID flags, `InstrumentID<>624`.
- **BI baseline (main tables)**
  - `Dim_Position`, `Dim_Instrument`, `Fact_SnapshotCustomer`, `Dim_Range`, `regulation_report_excluded_cids`.
  - Filters: `RegulationID IN (4,10)`, MiFID instrument scope, `InstrumentID<>624`, `IsMifid=1`, `IsSettled=0`, distinct trade identity.

### 4.5 MiFID EU SC

- **Audit table**
  - `dbo.MIFID2_Report` with `RegulationID=9`, `RegulationReportID=1`, `OpenORClose IN ('C','O')`.
  - Transaction reference normalized by suffix trimming.
- **Mismatch counterpart**
  - `BestEX_Report` with `eToroEntity='eToro SC'`, MiFID instrument eligibility.
  - Missing-in-audit branch excludes `InstrumentID=624`.
- **Join keys**
  - `CID`, normalized transaction reference vs `TradeID`, `InstrumentID`, date.
- **Cleanup filters**
  - Migration cleanup with `PrevRegulationID=9` and `RegulationID=9`.
- **TraNa baseline**
  - `RegulationAggTrans` with `eToroEntity='eToro SC'`, `ClientOpen/ClientClose`, MiFID flags, `InstrumentID<>624`.
- **BI baseline (main tables)**
  - `Dim_Position`, `Dim_Instrument`, `Fact_SnapshotCustomer`, `Dim_Range`, `regulation_report_excluded_cids`.
  - Filters: `RegulationID IN (9)`, MiFID instrument scope, `InstrumentID<>624`, `IsMifid=1`.

### 4.6 MiFID EU ME

- **Audit table**
  - `dbo.MIFID2_ME_Report` with `RegulationID=11`, `RegulationReportID=1`, `OpenORClose IN ('C','O')`.
- **Mismatch counterpart**
  - `BestEX_Report` with `eToroEntity='eToro ME'`, MiFID instrument eligibility.
  - Missing-in-audit branch excludes `InstrumentID=624`.
- **Join keys**
  - `CID`, normalized transaction reference vs `TradeID`, `InstrumentID`, date.
- **Cleanup filters**
  - Migration cleanup with `PrevRegulationID=11` and `RegulationID=11`.
- **TraNa baseline**
  - `RegulationAggTrans` with `eToroEntity='eToro ME'`, `ClientOpen/ClientClose`, MiFID flags, `InstrumentID<>624`.
- **BI baseline (main tables)**
  - `Dim_Position`, `Dim_Instrument`, `Fact_SnapshotCustomer`, `Dim_Range`, `regulation_report_excluded_cids`.
  - Filters: `RegulationID IN (11)`, MiFID instrument scope, `InstrumentID<>624`, `IsMifid=1`.

### 4.7 MiFID EU FCA

- **Audit table**
  - `dbo.MIFID2_Report` with `RegulationID=2`, `RegulationReportID=1`, `OpenORClose IN ('C','O')`.
  - Transaction reference normalized using `REPLACE(TransactionReferenceNumber,'UK','')`.
- **Mismatch counterpart**
  - `BestEX_Report` with `eToroEntity='eToro UK'`, MiFID+FCA instrument eligibility (`IsMifid=1`, `IsMifidByFCA=1` in SCD).
- **Join keys**
  - `CID`, normalized transaction reference vs `TradeID`, `InstrumentID`, date.
- **Cleanup filters**
  - Migration cleanup with `PrevRegulationID=2` and `RegulationID=2`.
- **TraNa baseline**
  - `RegulationAggTrans` with `eToroEntity='eToro UK'`, `ClientOpen/ClientClose`, MiFID flags, `InstrumentID<>624`.
- **BI baseline (main tables)**
  - `Dim_Position`, `Dim_Instrument`, `Fact_SnapshotCustomer`, `Dim_Range`, `regulation_report_excluded_cids`.
  - Filters: `RegulationID IN (2)`, MiFID instrument scope, `IsMifid=1`, `IsMifidByFCA=1`.

## 5) EMIR flows (5)

### 5.1 EMIR TR CL

- **Audit table**
  - `dbo.EMIR2_Refit_Report`
  - Filters: `Level='TCTN'`, `RegulationID IN (1,2)`, `FlippedReport=0`, `OpenORClose='O'`.
- **Mismatch counterpart**
  - `BestEX_Report` with `eToroEntity IN ('eToro EU','eToro UK')`, `OpenORClose='O'`, `[CFD/Real]='CFD'`.
- **Join keys**
  - `CID`, `PositionID`, `InstrumentID`, `ReportDate=Trade_date`.
- **Cleanup filters**
  - Reg-movement exclusions for `PrevRegulationID IN (1,2)` and `RegulationID IN (1,2)`.
- **TraNa baseline**
  - `RegulationAggTrans` with `eToroEntity IN ('eToro EU','eToro UK')`, `[CFD/Real]='CFD'`, `OpenORClose='ClientOpen'`, MiFID flags permissive.
- **BI baseline (main tables)**
  - `Dim_Position`, `Dim_Instrument`, `Fact_SnapshotCustomer`, `Dim_Range`, `regulation_report_excluded_cids`.
  - Filters: `RegulationID IN (1,2)`, open-leg scope, `IsSettled=0`, distinct trade identity.

### 5.2 EMIR TR AUS

- **Audit table**
  - `dbo.EMIR2_ETORO_Refit_Trades` with `Level='TCTN'`, `RegulationID IN (4,10)`, `FlippedReport=0`, `OpenORClose='O'`.
- **Mismatch counterpart**
  - `BestEX_Report` with `eToroEntity='eToro AUS'`, `OpenORClose='O'`, `[CFD/Real]='CFD'`.
- **Join keys**
  - `CID`, `PositionID`, `InstrumentID`, date.
- **Cleanup filters**
  - Current procedure removes audit-side rows where `PositionID` appears in `Reg_Regulation_Movments_Positions` for the date window.
- **TraNa baseline**
  - `RegulationAggTrans` with `eToroEntity='eToro AUS'`, `[CFD/Real]='CFD'`, `OpenORClose='ClientOpen'`.
- **BI baseline (main tables)**
  - `Dim_Position`, `Dim_Instrument`, `Fact_SnapshotCustomer`, `Dim_Range`, `regulation_report_excluded_cids`.
  - Filters: `RegulationID IN (4,10)`, open-leg scope, `IsSettled=0`, distinct trade identity.

### 5.3 EMIR TR SC

- **Audit table**
  - `dbo.EMIR2_Refit_Report` with `Level='TCTN'`, `RegulationID IN (9)`, `FlippedReport=0`, `OpenORClose='O'`.
- **Mismatch counterpart**
  - `BestEX_Report` with `eToroEntity='eToro SC'`, `OpenORClose='O'`, `[CFD/Real]='CFD'`.
- **Join keys**
  - `CID`, `PositionID`, `InstrumentID`, date.
- **Cleanup filters**
  - Reg-movement exclusions with `PrevRegulationID=9` and `RegulationID=9`.
- **TraNa baseline**
  - `RegulationAggTrans` with `eToroEntity='eToro SC'`, `OpenORClose='ClientOpen'`, `[CFD/Real]='CFD'`.
- **BI baseline (main tables)**
  - `Dim_Position`, `Dim_Instrument`, `Fact_SnapshotCustomer`, `Dim_Range`, `regulation_report_excluded_cids`.
  - Filters: `RegulationID IN (9)`, open-leg scope, `IsSettled=0`, distinct trade identity.

### 5.4 EMIR TR ME

- **Audit table**
  - `dbo.EMIR3_ME_Refit_Report` with `Level='TCTN'`, `RegulationID IN (11)`, `FlippedReport=0`, `OpenORClose='O'`.
- **Mismatch counterpart**
  - `BestEX_Report` with `eToroEntity='eToro ME'`, `OpenORClose='O'`, `[CFD/Real]='CFD'`.
- **Join keys**
  - `CID`, `PositionID`, `InstrumentID`, date.
- **Cleanup filters**
  - Reg-movement exclusions with `PrevRegulationID=11` and `RegulationID=11`.
- **TraNa baseline**
  - `RegulationAggTrans` with `eToroEntity='eToro ME'`, `OpenORClose='ClientOpen'`, `[CFD/Real]='CFD'`.
- **BI baseline (main tables)**
  - `Dim_Position`, `Dim_Instrument`, `Fact_SnapshotCustomer`, `Dim_Range`, `regulation_report_excluded_cids`.
  - Filters: `RegulationID IN (11)`, open-leg scope, `IsSettled=0`, distinct trade identity.

### 5.5 EMIR POS CL

- **Audit table**
  - `dbo.EMIR2_Refit_Report`
  - Filters: `ReportDate=@ReportDate1`, `IsPosition=1`, `FlippedReport=0`, `RegulationID<>9`.
- **TraNa baseline**
  - Not applicable in current procedure (`TraNa_Transaction_Count` is null for POS flows).
- **BI baseline (main tables)**
  - `Dim_Position`, `Dim_Instrument`, `Fact_SnapshotCustomer`, `Dim_Range`, `regulation_report_excluded_cids`.
  - Filters:
    - `RegulationID IN (1,2)`,
    - position active on report date,
    - `CAST(OpenOccurred AS DATE) >= '2014-02-12'`,
    - `IsSettled=0`.
  - Count is based on grouped `(date, CID, InstrumentID)` population.

## 6) ASIC flows (3)

### 6.1 ASIC TR CL

- **Audit table**
  - `dbo.ASIC2_Transactions`
  - Filters: `RegulationID IN (4,10)`, `OpenORClose IN ('O','C')`.
  - Audit transaction reference derived as `CONCAT(PositionID, OpenORClose)`.
- **Mismatch counterpart**
  - `BestEX_Report` with `eToroEntity='eToro AUS'`, `[CFD/Real]='CFD'`, `OpenORClose IN ('O','C')`.
- **Join keys**
  - `CID`, audit transaction reference vs `TradeID`, `InstrumentID`, date, and `OpenORClose`.
- **Cleanup filters**
  - Remove synthetic/migration-expected rows using:
    - `Reg_Regulation_Movments_Positions` (generic + regulation-specific checks),
    - `Reg_RegulationInOutDailyData` (`PrevRegulationID`/`RegulationID IN (4,10)` and migration timing checks).
- **TraNa baseline**
  - `RegulationAggTrans` with `eToroEntity='eToro AUS'`, `[CFD/Real]='CFD'`, `OpenORClose IN ('ClientOpen','ClientClose')`.
- **BI baseline (main tables)**
  - `Dim_Position`, `Dim_Instrument`, `Fact_SnapshotCustomer`, `Dim_Range`, `regulation_report_excluded_cids`.
  - Filters: `RegulationID IN (4,10)`, open/close leg scope, `IsSettled=0`, distinct trade identity.

### 6.2 ASIC TR EU

- **Audit table**
  - `dbo.ASIC2_Transactions` with same filters as ASIC TR CL.
- **Mismatch counterpart**
  - `BestEX_Report` with same AUS filters as ASIC TR CL.
- **Join keys**
  - Same as ASIC TR CL (`CID`, trade reference, instrument, date, open/close).
- **Cleanup filters**
  - Same migration/synthetic cleanup pattern as ASIC TR CL.
- **TraNa baseline**
  - Same `RegulationAggTrans` filters as ASIC TR CL.
- **BI baseline (main tables)**
  - Same main-table sources and filters as ASIC TR CL (`Dim_Position`, `Dim_Instrument`, `Fact_SnapshotCustomer`, `Dim_Range`, exclusions table).
- **Implementation note**
  - Current stored procedure logic for ASIC TR CL and ASIC TR EU uses the same table/filter pattern; operational naming differs by regime label in outputs.

### 6.3 ASIC POS CL

- **Audit table**
  - `dbo.ASIC2_Positions_AGG`
  - Filter: `ReportDate=@ReportDate1`.
- **TraNa baseline**
  - Not applicable in current procedure (`TraNa_Transaction_Count` is null for POS flows).
- **BI baseline (main tables)**
  - `Dim_Position`, `Dim_Instrument`, `Fact_SnapshotCustomer`, `Dim_Range`, `regulation_report_excluded_cids`.
  - Filters:
    - `RegulationID IN (4,10)`,
    - position active on report date,
    - `IsSettled=0`,
    - count over grouped `(date, CID, InstrumentID)` rows.

## 7) BI implementation detail (how helper temp tables are created)

Primary BI source-of-truth tables are:

- `[SYNAPSE-DWH-PROD].[sql_dp_prod_we].[DWH_dbo].[Dim_Position]`
- `[SYNAPSE-DWH-PROD].[sql_dp_prod_we].[DWH_dbo].[Dim_Instrument]`
- `[SYNAPSE-DWH-PROD].[sql_dp_prod_we].[DWH_dbo].[Fact_SnapshotCustomer]`
- `[SYNAPSE-DWH-PROD].[sql_dp_prod_we].[DWH_dbo].[Dim_Range]`
- `[ThirdParty_Fivetran].[Fivetran].[regtech].[regulation_report_excluded_cids]`

The stored procedure then materializes helper temp tables from those sources, as follows:

### 7.1 `#TR` (transactional helper from main BI tables)

`#TR` is created from `Dim_Position` (with `Dim_Instrument` and `Reg_Instruments_SCD` enrichment) in three inserts:

1. Open legs for new positions (`OriginalPositionID IS NULL`),
2. Open legs for rolled positions (`OriginalPositionID IS NOT NULL` and `PositionID=OriginalPositionID`),
3. Close legs (`CloseDateID` in date range).

Enrichment from `Reg_Instruments_SCD` contributes:

- `InstrumentTypeID`,
- `IsMifidByFCA`,
- `IsMifid`.

### 7.2 `#POS` (position helper from main BI tables)

Built from open positions active on `@ReportDate1ID`:

- `OpenDateID <= @ReportDate1ID`
- and `(CloseDateID = 0 OR CloseDateID > @ReportDate1ID)`.

### 7.3 Customer/date eligibility helpers (`#DR`, `#CID`, `#FSC`)

- `#DR` from `Dim_Range` overlapping the audit date window.
- `#CID` built from transaction/position helper populations, excluding CIDs in Fivetran exclusion list.
- `#FSC` from `Fact_SnapshotCustomer` with eligibility filters listed in Section 3.

## 8) How to use this appendix operationally

For any exception in `DailyCompleteness_AuditLog`:

1. Locate regime in Sections 4/5/6.
2. Validate that expected source filters match business intent.
3. Re-check join keys and migration cleanup applicability.
4. Confirm BI eligibility filters did not over/under-filter population.
5. Escalate to Step 2B field lineage only after record-level logic is validated.
