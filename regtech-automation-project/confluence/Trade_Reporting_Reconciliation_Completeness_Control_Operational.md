# Step 2C - Operational Completeness Reconciliation Control (Daily Audit)

Last updated: 2026-03-18  
Workstream: REG-3279 Step 2C (operational completeness)  
Owner: Reg Ops + Data Engineering

## 1) Purpose

This document defines the operational completeness control implemented by:

- `dbo.usp_DailyCompleteness_Audit`

The control answers:

- Are expected reporting records present in internal reporting tables?
- Do internal reporting counts reconcile to operational (TraNa/Ops) baselines?
- Do internal reporting counts reconcile to BI source-of-truth baselines?

This is the runtime counterpart to Step 2B (field lineage):

- Step 2B = design-time field mapping completeness.
- Step 2C = run-time record completeness control.

## 2) Relationship to Step 2A and Step 2B

| Step | Artifact purpose | Core question answered |
|---|---|---|
| Step 2A | Source inventory catalog | Which systems/tables/files exist? |
| Step 2B | Field-level mapping matrix | How is each field derived and reconciled? |
| Step 2C | Daily operational completeness control | Did all expected records appear across Audit vs TraNa vs BI? |

## 3) Scope covered by `usp_DailyCompleteness_Audit`

The procedure currently computes daily controls for:

1. MiFID UK CL  
2. MiFID EU CL  
3. MiFID EU Hedge  
4. MiFID EU AUS  
5. MiFID EU SC  
6. MiFID EU ME  
7. MiFID EU FCA  
8. EMIR TR CL  
9. EMIR TR AUS  
10. EMIR TR SC  
11. EMIR TR ME  
12. ASIC TR CL  
13. ASIC TR EU  
14. EMIR POS CL  
15. ASIC POS CL

## 4) Reconciliation model (three-way)

The control compares three independently derived baselines:

- **Audit baseline**: reporting-table population counts and cleaned mismatch sets.
- **TraNa/Ops baseline**: operational transaction aggregates (for eligible flows).
- **BI baseline**: independent DWH-derived population counts (Synapse/BI pipeline logic), subject to the current instrument-eligibility dependency noted below.

Control priority for completeness decisions:

1. **Primary KPI**: `Audit_vs_BI_Completeness` (BI-prioritized completeness baseline),
2. **Secondary KPI**: `Audit_vs_TraNa_Completeness` (operational cross-check),
3. **Diagnostic layer**: BestEX record-set mismatches (where applicable) for exception triage/root cause.

```mermaid
flowchart LR
    A[Audit reporting tables<br/>MIFID2_*, EMIR2_*, ASIC2_*] --> R[Daily completeness engine<br/>usp_DailyCompleteness_Audit]
    B[Ops/TraNa baseline<br/>RegulationAggTrans] --> R
    C[BI source-of-truth baseline<br/>Synapse Dim_Position/Fact_SnapshotCustomer/Hedge logs] --> R
    R --> D[DailyCompleteness_AuditLog]
    D --> E[Operations dashboard / exception workflow]
```

### 4.1 Regime-by-regime comparison matrix (BI prioritized)

Shared BI eligibility filters (apply to all non-hedge BI rows):

- `Fact_SnapshotCustomer.PlayerLevelID <> 4`
- `Fact_SnapshotCustomer.IsValidCustomer = 1`
- `Fact_SnapshotCustomer.AccountTypeID NOT IN (7,9)`
- `Fact_SnapshotCustomer.CountryID <> 250`
- exclusion via `regulation_report_excluded_cids.cid IS NULL`

| Regime | BI source tables used for count | BI filter fields (table.column) | BI filter criteria (regime-specific) | Primary completeness comparison | Secondary comparison | BestEX diagnostic | BestEX filter fields (table.column) | BestEX filter criteria |
|---|---|---|---|---|---|---|---|---|
| MiFID UK CL | `Dim_Position`, `Reg_Instruments_SCD`, `Fact_SnapshotCustomer`, `Dim_Range`, `regulation_report_excluded_cids` | `Fact_SnapshotCustomer.RegulationID`; `Dim_Position.InstrumentID`; `Reg_Instruments_SCD.InstrumentTypeID`; `Reg_Instruments_SCD.IsMifidByFCA` | `RegulationID=2`; `(InstrumentID IN (319,341) OR InstrumentTypeID IN (4,5,6))`; `IsMifidByFCA=1` | Audit vs BI (`Audit_vs_BI_Completeness`) | Audit vs TraNa | Yes | `BestEX_Report.Trade_date/eToroEntity/OpenORClose/InstrumentID`; `Reg_Instruments_SCD.ValidFrom/ValidTo/IsMifidByFCA` | `Trade_date` in range; `eToroEntity='eToro UK'`; `OpenORClose IN ('C','O')`; date-valid SCD instrument with `IsMifidByFCA=1` |
| MiFID EU CL | same core BI tables as above | `Fact_SnapshotCustomer.RegulationID`; `Dim_Position.InstrumentID`; `Reg_Instruments_SCD.InstrumentTypeID`; `Reg_Instruments_SCD.IsMifid` | `RegulationID=1`; `(InstrumentID IN (319,341) OR InstrumentTypeID IN (4,5,6))`; `InstrumentID<>624`; `IsMifid=1` | Audit vs BI (`Audit_vs_BI_Completeness`) | Audit vs TraNa | Yes | `BestEX_Report.Trade_date/eToroEntity/OpenORClose/InstrumentID`; `Reg_Instruments_SCD.ValidFrom/ValidTo/IsMifid` | `Trade_date` in range; `eToroEntity='eToro EU'`; `OpenORClose IN ('C','O')`; date-valid SCD instrument with `IsMifid=1`; `InstrumentID<>624` in missing-in-audit branch |
| MiFID EU Hedge | `Hedge.ExecutionLog`, `Reg_Ext_LiquidityAccountID`, `Reg_LiquidtyAcount_SCD`, `Reg_Instruments_SCD` | `ExecutionLog.ExecutionTime/Units/Success/ProviderExecID/OrderState`; `Reg_Ext_LiquidityAccountID.eToroEntity`; `Reg_Instruments_SCD.IsMifid` | date in range; `Units>0`; `Success=1`; not(`ProviderExecID IS NULL` and `OrderState=4`); LP entity in EU/UK set; MiFID instrument scope | Audit vs BI (`Audit_vs_BI_Completeness`) | Audit vs TraNa | No | N/A | N/A |
| MiFID EU AUS | same core BI tables as MiFID UK/EU | `Fact_SnapshotCustomer.RegulationID`; `Dim_Position.IsSettled`; `Reg_Instruments_SCD.IsMifid`; instrument fields above | `RegulationID IN (4,10)`; MiFID instrument scope; `InstrumentID<>624`; `IsMifid=1`; `IsSettled=0` | Audit vs BI (`Audit_vs_BI_Completeness`) | Audit vs TraNa | Yes | `BestEX_Report.Trade_date/eToroEntity/[CFD/Real]/OpenORClose/InstrumentID`; `Reg_Instruments_SCD.ValidFrom/ValidTo/IsMifid` | `Trade_date` in range; `eToroEntity='eToro AUS'`; `[CFD/Real]='CFD'`; `OpenORClose IN ('C','O')`; date-valid SCD instrument with `IsMifid=1`; `InstrumentID<>624` in missing-in-audit branch |
| MiFID EU SC | same core BI tables as MiFID UK/EU | `Fact_SnapshotCustomer.RegulationID`; instrument fields above; `Reg_Instruments_SCD.IsMifid` | `RegulationID=9`; MiFID instrument scope; `InstrumentID<>624`; `IsMifid=1` | Audit vs BI (`Audit_vs_BI_Completeness`) | Audit vs TraNa | Yes | `BestEX_Report.Trade_date/eToroEntity/OpenORClose/InstrumentID`; `Reg_Instruments_SCD.ValidFrom/ValidTo/IsMifid` | `Trade_date` in range; `eToroEntity='eToro SC'`; `OpenORClose IN ('C','O')`; date-valid SCD instrument with `IsMifid=1`; `InstrumentID<>624` in missing-in-audit branch |
| MiFID EU ME | same core BI tables as MiFID UK/EU | `Fact_SnapshotCustomer.RegulationID`; instrument fields above; `Reg_Instruments_SCD.IsMifid` | `RegulationID=11`; MiFID instrument scope; `InstrumentID<>624`; `IsMifid=1` | Audit vs BI (`Audit_vs_BI_Completeness`) | Audit vs TraNa | Yes | `BestEX_Report.Trade_date/eToroEntity/OpenORClose/InstrumentID`; `Reg_Instruments_SCD.ValidFrom/ValidTo/IsMifid` | `Trade_date` in range; `eToroEntity='eToro ME'`; `OpenORClose IN ('C','O')`; date-valid SCD instrument with `IsMifid=1`; `InstrumentID<>624` in missing-in-audit branch |
| MiFID EU FCA | same core BI tables as MiFID UK/EU | `Fact_SnapshotCustomer.RegulationID`; instrument fields above; `Reg_Instruments_SCD.IsMifid`; `Reg_Instruments_SCD.IsMifidByFCA` | `RegulationID=2`; MiFID instrument scope; `IsMifid=1`; `IsMifidByFCA=1` | Audit vs BI (`Audit_vs_BI_Completeness`) | Audit vs TraNa | Yes | `BestEX_Report.Trade_date/eToroEntity/OpenORClose/InstrumentID`; `Reg_Instruments_SCD.ValidFrom/ValidTo/IsMifid/IsMifidByFCA` | `Trade_date` in range; `eToroEntity='eToro UK'`; `OpenORClose IN ('C','O')`; date-valid SCD instrument with `IsMifid=1` and `IsMifidByFCA=1` |
| EMIR TR CL | `Dim_Position`, `Fact_SnapshotCustomer`, `Dim_Range`, `regulation_report_excluded_cids` | `Fact_SnapshotCustomer.RegulationID`; leg-derived `OpenORClose`; `Dim_Position.IsSettled` | `RegulationID IN (1,2)`; open-leg scope; `IsSettled=0` | Audit vs BI (`Audit_vs_BI_Completeness`) | Audit vs TraNa | Yes | `BestEX_Report.Trade_date/eToroEntity/OpenORClose/[CFD/Real]` | `Trade_date` in range; `eToroEntity IN ('eToro EU','eToro UK')`; `OpenORClose='O'`; `[CFD/Real]='CFD'` |
| EMIR TR AUS | same core BI tables as EMIR TR CL | `Fact_SnapshotCustomer.RegulationID`; leg-derived `OpenORClose`; `Dim_Position.IsSettled` | `RegulationID IN (4,10)`; open-leg scope; `IsSettled=0` | Audit vs BI (`Audit_vs_BI_Completeness`) | Audit vs TraNa | Yes | `BestEX_Report.Trade_date/eToroEntity/OpenORClose/[CFD/Real]` | `Trade_date` in range; `eToroEntity='eToro AUS'`; `OpenORClose='O'`; `[CFD/Real]='CFD'` |
| EMIR TR SC | same core BI tables as EMIR TR CL | `Fact_SnapshotCustomer.RegulationID`; leg-derived `OpenORClose`; `Dim_Position.IsSettled` | `RegulationID=9`; open-leg scope; `IsSettled=0` | Audit vs BI (`Audit_vs_BI_Completeness`) | Audit vs TraNa | Yes | `BestEX_Report.Trade_date/eToroEntity/OpenORClose/[CFD/Real]` | `Trade_date` in range; `eToroEntity='eToro SC'`; `OpenORClose='O'`; `[CFD/Real]='CFD'` |
| EMIR TR ME | same core BI tables as EMIR TR CL | `Fact_SnapshotCustomer.RegulationID`; leg-derived `OpenORClose`; `Dim_Position.IsSettled` | `RegulationID=11`; open-leg scope; `IsSettled=0` | Audit vs BI (`Audit_vs_BI_Completeness`) | Audit vs TraNa | Yes | `BestEX_Report.Trade_date/eToroEntity/OpenORClose/[CFD/Real]` | `Trade_date` in range; `eToroEntity='eToro ME'`; `OpenORClose='O'`; `[CFD/Real]='CFD'` |
| ASIC TR CL | `Dim_Position`, `Fact_SnapshotCustomer`, `Dim_Range`, `regulation_report_excluded_cids` | `Fact_SnapshotCustomer.RegulationID`; leg-derived `OpenORClose`; `Dim_Position.IsSettled` | `RegulationID IN (4,10)`; open+close leg scope; `IsSettled=0` | Audit vs BI (`Audit_vs_BI_Completeness`) | Audit vs TraNa | Yes | `BestEX_Report.Trade_date/eToroEntity/OpenORClose/[CFD/Real]` | `Trade_date` in range; `eToroEntity='eToro AUS'`; `OpenORClose IN ('O','C')`; `[CFD/Real]='CFD'` |
| ASIC TR EU | same core BI tables as ASIC TR CL | same as ASIC TR CL | same as ASIC TR CL | Audit vs BI (`Audit_vs_BI_Completeness`) | Audit vs TraNa | Yes | `BestEX_Report.Trade_date/eToroEntity/OpenORClose/[CFD/Real]` | `Trade_date` in range; `eToroEntity='eToro AUS'`; `OpenORClose IN ('O','C')`; `[CFD/Real]='CFD'` |
| EMIR POS CL | `Dim_Position`, `Fact_SnapshotCustomer`, `Dim_Range`, `regulation_report_excluded_cids` | `Fact_SnapshotCustomer.RegulationID`; `Dim_Position.OpenDateID`; `Dim_Position.CloseDateID`; `Dim_Position.OpenOccurred`; `Dim_Position.IsSettled` | `RegulationID IN (1,2)`; active position on report date; `OpenOccurred>='2014-02-12'`; `IsSettled=0` | Audit vs BI (`Audit_vs_BI_Completeness`) | Not applicable | No | N/A | N/A |
| ASIC POS CL | `Dim_Position`, `Fact_SnapshotCustomer`, `Dim_Range`, `regulation_report_excluded_cids` | `Fact_SnapshotCustomer.RegulationID`; `Dim_Position.OpenDateID`; `Dim_Position.CloseDateID`; `Dim_Position.IsSettled` | `RegulationID IN (4,10)`; active position on report date; `IsSettled=0` | Audit vs BI (`Audit_vs_BI_Completeness`) | Not applicable | No | N/A | N/A |

### 4.2 Exact filter values by regime for all comparisons

| Regime | Audit filter fields | Audit filter values | BI filter fields | BI filter values | TraNa filter fields | TraNa filter values | BestEX filter fields | BestEX filter values |
|---|---|---|---|---|---|---|---|---|
| MiFID UK CL | `MIFID2_Report.RegulationID/RegulationReportID/OpenORClose` | `RegulationID=2`; `RegulationReportID=2`; `OpenORClose IN ('C','O')` | `Fact_SnapshotCustomer.RegulationID`; `Dim_Position.InstrumentID`; `Reg_Instruments_SCD.InstrumentTypeID`; `Reg_Instruments_SCD.IsMifidByFCA` | `RegulationID=2`; `(InstrumentID IN (319,341) OR InstrumentTypeID IN (4,5,6))`; `IsMifidByFCA=1` | `RegulationAggTrans.eToroEntity/OpenORClose/IsMifidByFCA/IsMifidByESMA` | `eToroEntity='eToro UK'`; `OpenORClose IN ('ClientOpen','ClientClose')`; `IsMifidByFCA=1`; `IsMifidByESMA IN (0,1)` | `BestEX_Report.Trade_date/eToroEntity/OpenORClose/InstrumentID`; `Reg_Instruments_SCD.ValidFrom/ValidTo/IsMifidByFCA` | `Trade_date BETWEEN @ReportDate1 AND @ReportDate2`; `eToroEntity='eToro UK'`; `OpenORClose IN ('C','O')`; date-valid SCD instrument; `IsMifidByFCA=1` |
| MiFID EU CL | `MIFID2_Report.RegulationID/RegulationReportID/OpenORClose` | `RegulationID=1`; `RegulationReportID=1`; `OpenORClose IN ('C','O')` | `Fact_SnapshotCustomer.RegulationID`; instrument scope fields; `Reg_Instruments_SCD.IsMifid` | `RegulationID=1`; `(InstrumentID IN (319,341) OR InstrumentTypeID IN (4,5,6))`; `InstrumentID<>624`; `IsMifid=1` | `RegulationAggTrans.eToroEntity/OpenORClose/IsMifidByESMA/IsMifidByFCA/InstrumentID` | `eToroEntity='eToro EU'`; `OpenORClose IN ('ClientOpen','ClientClose')`; `IsMifidByESMA=1`; `IsMifidByFCA IN (0,1)`; `InstrumentID<>624` | `BestEX_Report.Trade_date/eToroEntity/OpenORClose/InstrumentID`; `Reg_Instruments_SCD.ValidFrom/ValidTo/IsMifid` | `Trade_date` in range; `eToroEntity='eToro EU'`; `OpenORClose IN ('C','O')`; date-valid SCD instrument; `IsMifid=1`; `InstrumentID<>624` in missing-in-audit branch |
| MiFID EU Hedge | `MIFID2_Hedge_Report.RegulationReportID` | `RegulationReportID=1` | `ExecutionLog.ExecutionTime/Units/Success/ProviderExecID/OrderState`; LP/SCD fields | `ExecutionTime` in range; `Units>0`; `Success=1`; not(`ProviderExecID IS NULL` and `OrderState=4`); LP entity in EU/UK set; MiFID instrument scope | `RegulationAggTrans.eToroEntity/OpenORClose/IsMifidByESMA/IsMifidByFCA/InstrumentID` | `eToroEntity IN ('eToro EU','eToro UK')`; `OpenORClose='HedgeExecution'`; `IsMifidByESMA=1`; `IsMifidByFCA IN (0,1)`; `InstrumentID<>624` | N/A | N/A |
| MiFID EU AUS | `MIFID2_ETORO_Report.RegulationID/RegulationReportID/OpenORClose` | `RegulationID=1`; `RegulationReportID=1`; `OpenORClose IN ('C','O')` | `Fact_SnapshotCustomer.RegulationID`; instrument scope; `Reg_Instruments_SCD.IsMifid`; `Dim_Position.IsSettled` | `RegulationID IN (4,10)`; MiFID scope; `InstrumentID<>624`; `IsMifid=1`; `IsSettled=0` | `RegulationAggTrans.eToroEntity/OpenORClose/[CFD/Real]/IsMifidByESMA/IsMifidByFCA/InstrumentID` | `eToroEntity='eToro AUS'`; `OpenORClose IN ('ClientOpen','ClientClose')`; `[CFD/Real]='CFD'`; `IsMifidByESMA=1`; `IsMifidByFCA IN (0,1)`; `InstrumentID<>624` | `BestEX_Report.Trade_date/eToroEntity/[CFD/Real]/OpenORClose/InstrumentID`; `Reg_Instruments_SCD.ValidFrom/ValidTo/IsMifid` | `Trade_date` in range; `eToroEntity='eToro AUS'`; `[CFD/Real]='CFD'`; `OpenORClose IN ('C','O')`; date-valid SCD instrument; `IsMifid=1`; `InstrumentID<>624` in missing-in-audit branch |
| MiFID EU SC | `MIFID2_Report.RegulationID/RegulationReportID/OpenORClose` | `RegulationID=9`; `RegulationReportID=1`; `OpenORClose IN ('C','O')` | `Fact_SnapshotCustomer.RegulationID`; instrument scope; `Reg_Instruments_SCD.IsMifid` | `RegulationID=9`; MiFID scope; `InstrumentID<>624`; `IsMifid=1` | `RegulationAggTrans.eToroEntity/OpenORClose/IsMifidByESMA/IsMifidByFCA/InstrumentID` | `eToroEntity='eToro SC'`; `OpenORClose IN ('ClientOpen','ClientClose')`; `IsMifidByESMA=1`; `IsMifidByFCA IN (0,1)`; `InstrumentID<>624` | `BestEX_Report.Trade_date/eToroEntity/OpenORClose/InstrumentID`; `Reg_Instruments_SCD.ValidFrom/ValidTo/IsMifid` | `Trade_date` in range; `eToroEntity='eToro SC'`; `OpenORClose IN ('C','O')`; date-valid SCD instrument; `IsMifid=1`; `InstrumentID<>624` in missing-in-audit branch |
| MiFID EU ME | `MIFID2_ME_Report.RegulationID/RegulationReportID/OpenORClose` | `RegulationID=11`; `RegulationReportID=1`; `OpenORClose IN ('C','O')` | `Fact_SnapshotCustomer.RegulationID`; instrument scope; `Reg_Instruments_SCD.IsMifid` | `RegulationID=11`; MiFID scope; `InstrumentID<>624`; `IsMifid=1` | `RegulationAggTrans.eToroEntity/OpenORClose/IsMifidByESMA/IsMifidByFCA/InstrumentID` | `eToroEntity='eToro ME'`; `OpenORClose IN ('ClientOpen','ClientClose')`; `IsMifidByESMA=1`; `IsMifidByFCA IN (0,1)`; `InstrumentID<>624` | `BestEX_Report.Trade_date/eToroEntity/OpenORClose/InstrumentID`; `Reg_Instruments_SCD.ValidFrom/ValidTo/IsMifid` | `Trade_date` in range; `eToroEntity='eToro ME'`; `OpenORClose IN ('C','O')`; date-valid SCD instrument; `IsMifid=1`; `InstrumentID<>624` in missing-in-audit branch |
| MiFID EU FCA | `MIFID2_Report.RegulationID/RegulationReportID/OpenORClose` | `RegulationID=2`; `RegulationReportID=1`; `OpenORClose IN ('C','O')` | `Fact_SnapshotCustomer.RegulationID`; instrument scope; `Reg_Instruments_SCD.IsMifid/IsMifidByFCA` | `RegulationID=2`; MiFID scope; `IsMifid=1`; `IsMifidByFCA=1` | `RegulationAggTrans.eToroEntity/OpenORClose/IsMifidByESMA/IsMifidByFCA/InstrumentID` | `eToroEntity='eToro UK'`; `OpenORClose IN ('ClientOpen','ClientClose')`; `IsMifidByESMA=1`; `IsMifidByFCA IN (0,1)`; `InstrumentID<>624` | `BestEX_Report.Trade_date/eToroEntity/OpenORClose/InstrumentID`; `Reg_Instruments_SCD.ValidFrom/ValidTo/IsMifid/IsMifidByFCA` | `Trade_date` in range; `eToroEntity='eToro UK'`; `OpenORClose IN ('C','O')`; date-valid SCD instrument; `IsMifid=1`; `IsMifidByFCA=1` |
| EMIR TR CL | `EMIR2_Refit_Report.Level/RegulationID/FlippedReport/OpenORClose` | `Level='TCTN'`; `RegulationID IN (1,2)`; `FlippedReport=0`; `OpenORClose='O'` | `Fact_SnapshotCustomer.RegulationID`; open-leg filters; `Dim_Position.IsSettled` | `RegulationID IN (1,2)`; open-leg scope; `IsSettled=0` | `RegulationAggTrans.eToroEntity/[CFD/Real]/OpenORClose/IsMifidByESMA/IsMifidByFCA` | `eToroEntity IN ('eToro EU','eToro UK')`; `[CFD/Real]='CFD'`; `OpenORClose='ClientOpen'`; `IsMifidByESMA IN (0,1)`; `IsMifidByFCA IN (0,1)` | `BestEX_Report.Trade_date/eToroEntity/OpenORClose/[CFD/Real]` | `Trade_date` in range; `eToroEntity IN ('eToro EU','eToro UK')`; `OpenORClose='O'`; `[CFD/Real]='CFD'` |
| EMIR TR AUS | `EMIR2_ETORO_Refit_Trades.Level/RegulationID/FlippedReport/OpenORClose` | `Level='TCTN'`; `RegulationID IN (4,10)`; `FlippedReport=0`; `OpenORClose='O'` | `Fact_SnapshotCustomer.RegulationID`; open-leg filters; `Dim_Position.IsSettled` | `RegulationID IN (4,10)`; open-leg scope; `IsSettled=0` | `RegulationAggTrans.eToroEntity/[CFD/Real]/OpenORClose/IsMifidByESMA/IsMifidByFCA` | `eToroEntity='eToro AUS'`; `[CFD/Real]='CFD'`; `OpenORClose='ClientOpen'`; `IsMifidByESMA IN (0,1)`; `IsMifidByFCA IN (0,1)` | `BestEX_Report.Trade_date/eToroEntity/OpenORClose/[CFD/Real]` | `Trade_date` in range; `eToroEntity='eToro AUS'`; `OpenORClose='O'`; `[CFD/Real]='CFD'` |
| EMIR TR SC | `EMIR2_Refit_Report.Level/RegulationID/FlippedReport/OpenORClose` | `Level='TCTN'`; `RegulationID=9`; `FlippedReport=0`; `OpenORClose='O'` | `Fact_SnapshotCustomer.RegulationID`; open-leg filters; `Dim_Position.IsSettled` | `RegulationID=9`; open-leg scope; `IsSettled=0` | `RegulationAggTrans.eToroEntity/[CFD/Real]/OpenORClose/IsMifidByESMA/IsMifidByFCA` | `eToroEntity='eToro SC'`; `[CFD/Real]='CFD'`; `OpenORClose='ClientOpen'`; `IsMifidByESMA IN (0,1)`; `IsMifidByFCA IN (0,1)` | `BestEX_Report.Trade_date/eToroEntity/OpenORClose/[CFD/Real]` | `Trade_date` in range; `eToroEntity='eToro SC'`; `OpenORClose='O'`; `[CFD/Real]='CFD'` |
| EMIR TR ME | `EMIR3_ME_Refit_Report.Level/RegulationID/FlippedReport/OpenORClose` | `Level='TCTN'`; `RegulationID=11`; `FlippedReport=0`; `OpenORClose='O'` | `Fact_SnapshotCustomer.RegulationID`; open-leg filters; `Dim_Position.IsSettled` | `RegulationID=11`; open-leg scope; `IsSettled=0` | `RegulationAggTrans.eToroEntity/[CFD/Real]/OpenORClose/IsMifidByESMA/IsMifidByFCA` | `eToroEntity='eToro ME'`; `[CFD/Real]='CFD'`; `OpenORClose='ClientOpen'`; `IsMifidByESMA IN (0,1)`; `IsMifidByFCA IN (0,1)` | `BestEX_Report.Trade_date/eToroEntity/OpenORClose/[CFD/Real]` | `Trade_date` in range; `eToroEntity='eToro ME'`; `OpenORClose='O'`; `[CFD/Real]='CFD'` |
| ASIC TR CL | `ASIC2_Transactions.RegulationID/OpenORClose` | `RegulationID IN (4,10)`; `OpenORClose IN ('O','C')` | `Fact_SnapshotCustomer.RegulationID`; open+close leg filters; `Dim_Position.IsSettled` | `RegulationID IN (4,10)`; open+close leg scope; `IsSettled=0` | `RegulationAggTrans.eToroEntity/[CFD/Real]/OpenORClose` | `eToroEntity='eToro AUS'`; `[CFD/Real]='CFD'`; `OpenORClose IN ('ClientOpen','ClientClose')` | `BestEX_Report.Trade_date/eToroEntity/OpenORClose/[CFD/Real]` | `Trade_date` in range; `eToroEntity='eToro AUS'`; `OpenORClose IN ('O','C')`; `[CFD/Real]='CFD'` |
| ASIC TR EU | `ASIC2_Transactions.RegulationID/OpenORClose` | `RegulationID IN (4,10)`; `OpenORClose IN ('O','C')` | `Fact_SnapshotCustomer.RegulationID`; open+close leg filters; `Dim_Position.IsSettled` | `RegulationID IN (4,10)`; open+close leg scope; `IsSettled=0` | `RegulationAggTrans.eToroEntity/[CFD/Real]/OpenORClose` | `eToroEntity='eToro AUS'`; `[CFD/Real]='CFD'`; `OpenORClose IN ('ClientOpen','ClientClose')` | `BestEX_Report.Trade_date/eToroEntity/OpenORClose/[CFD/Real]` | `Trade_date` in range; `eToroEntity='eToro AUS'`; `OpenORClose IN ('O','C')`; `[CFD/Real]='CFD'` |
| EMIR POS CL | `EMIR2_Refit_Report.ReportDate/IsPosition/FlippedReport/RegulationID` | `ReportDate=@ReportDate1`; `IsPosition=1`; `FlippedReport=0`; `RegulationID<>9` | `Fact_SnapshotCustomer.RegulationID`; active-position fields; `Dim_Position.OpenOccurred`; `Dim_Position.IsSettled` | `RegulationID IN (1,2)`; active position; `OpenOccurred>='2014-02-12'`; `IsSettled=0` | N/A | N/A | N/A | N/A |
| ASIC POS CL | `ASIC2_Positions_AGG.ReportDate` | `ReportDate=@ReportDate1` | `Fact_SnapshotCustomer.RegulationID`; active-position fields; `Dim_Position.IsSettled` | `RegulationID IN (4,10)`; active position; `IsSettled=0` | N/A | N/A | N/A | N/A |

## 5) Key source tables used by the control

### 5.1 Audit-side reporting outputs

- `dbo.MIFID2_Report`
- `dbo.MIFID2_ETORO_Report`
- `dbo.MIFID2_ME_Report`
- `dbo.MIFID2_Hedge_Report`
- `dbo.EMIR2_Refit_Report`
- `dbo.EMIR2_ETORO_Refit_Trades`
- `dbo.EMIR3_ME_Refit_Report`
- `dbo.ASIC2_Transactions`
- `dbo.ASIC2_Positions_AGG`

### 5.2 Operational / TraNa counts

- `dbo.RegulationAggTrans`

### 5.3 BI source-of-truth components

- `[SYNAPSE-DWH-PROD].[sql_dp_prod_we].[DWH_dbo].[Dim_Position]`
- `[SYNAPSE-DWH-PROD].[sql_dp_prod_we].[DWH_dbo].[Dim_Instrument]`
- `[SYNAPSE-DWH-PROD].[sql_dp_prod_we].[DWH_dbo].[Fact_SnapshotCustomer]`
- `[SYNAPSE-DWH-PROD].[sql_dp_prod_we].[DWH_dbo].[Dim_Range]`
- `[AZR-W-REAL-DB-2-BIDBUser].[etoro].[Hedge].[ExecutionLog]`

Implementation note:

- BI helper temp tables used inside the procedure are documented separately in:
  - `Trade_Reporting_Reconciliation_Completeness_Control_Operational_Appendix.md` (Section 7)

### 5.4 Filter and exclusion controls

- `dbo.Reg_Instruments_SCD`
- `dbo.Reg_Regulation_Movments_Positions`
- `dbo.Reg_RegulationInOutDailyData`
- `[ThirdParty_Fivetran].[Fivetran].[regtech].[regulation_report_excluded_cids]`

### 5.5 Independence caveat (current state)

For MiFID/FCA eligibility filtering in Step 2C (`IsMifid`, `IsMifidByFCA`, and date-valid instrument joins), the control currently depends on:

- `dbo.Reg_Instruments_SCD`

This is a shared internal reference also used in reporting-table creation logic.  
Therefore, instrument eligibility validation is not yet fully independent from the reporting pipeline for these flags.

Planned enhancement path:

- Introduce independent external reference validation using:
  - ESMA FIRDS: `https://registers.esma.europa.eu/publication/searchRegister?core=esma_registers_firds#`
  - FCA reference data: `https://data.fca.org.uk/#/viewdata`

## 6) Core output metrics

For each `ReportDate` + `Regime`, the procedure persists:

- `Audit_Transaction_Count`
- `TraNa_Transaction_Count`
- `BI_Transaction_Count`
- `Audit_vs_TraNa_Mismatch`
- `Audit_vs_BI_Mismatch`
- `BI_vs_TraNa_Mismatch`
- `Clean_Missing_In_Audit`
- `Clean_Extra_In_Audit`
- `Clean_Mismatch_Total`
- `FalsePositives_Estimated`
- `Audit_vs_TraNa_Completeness`
- `Audit_vs_BI_Completeness`
- `Hedge_Mismatch_Is_FalsePositive_Flag`

### 6.1 Formula definitions

- `Audit_vs_TraNa_Mismatch = Audit_Transaction_Count - TraNa_Transaction_Count`
- `Audit_vs_BI_Mismatch = Audit_Transaction_Count - BI_Transaction_Count`
- `BI_vs_TraNa_Mismatch = BI_Transaction_Count - TraNa_Transaction_Count` (null where TraNa not applicable)
- `Audit_vs_TraNa_Completeness = (TraNa_Transaction_Count - Clean_Missing_In_Audit) / TraNa_Transaction_Count`
- `Audit_vs_BI_Completeness = Audit_Transaction_Count / BI_Transaction_Count`

Note:

- MiFID EU Hedge has explicit false-positive logic in the procedure: when BI and Audit match, hedge mismatch can be marked as non-defect (`Hedge_Mismatch_Is_FalsePositive_Flag=1`).

## 7) Data quality normalization and false-positive reduction

Before final metrics are calculated, intermediate mismatch datasets are cleaned by:

- migration-window exclusions (`OpenOccurred`, `ExecutionTime`, `Migration_Occurred` checks),
- regulation movement exclusions (PrevRegulationID / RegulationID transitions),
- synthetic/open-close suppression in affected flows,
- known-customer exclusion filters from Fivetran reference.

This allows:

- raw mismatch (signal),
- cleaned mismatch (actionable signal),
- false-positive estimate (noise control).

## 8) Procedure runbook

### 8.1 Standard daily run

```sql
EXEC dbo.usp_DailyCompleteness_Audit
    @AsOfDate = NULL,
    @ReturnResults = 0;
```

### 8.2 Backfill or ad-hoc run

```sql
EXEC dbo.usp_DailyCompleteness_Audit
    @AsOfDate = '2026-03-18',
    @ReturnResults = 1;
```

### 8.3 Output table

Run results are persisted to:

- `dbo.DailyCompleteness_AuditLog`

Recommended operational query pattern:

```sql
SELECT TOP (500)
       RunDtmUtc,
       ReportDate,
       Regime,
       Audit_Transaction_Count,
       TraNa_Transaction_Count,
       BI_Transaction_Count,
       Audit_vs_TraNa_Completeness,
       Audit_vs_BI_Completeness,
       Clean_Mismatch_Total
FROM dbo.DailyCompleteness_AuditLog
ORDER BY RunDtmUtc DESC, ReportDate DESC, OrderID;
```

## 9) Management presentation format

For manager updates, present Step 2C as:

1. **Coverage**: regimes included (15)
2. **Latest run health (BI-prioritized)**: count of green/amber/red regimes based first on `Audit_vs_BI_Completeness`
3. **Secondary health view**: `Audit_vs_TraNa_Completeness` drift and diagnostic mismatch behavior
4. **Top exceptions**: highest `Clean_Mismatch_Total` and lowest completeness
5. **Action owners**: named owner and target action per exception
6. **Trend**: 5-day trend of `Audit_vs_BI_Completeness` (primary) and `Audit_vs_TraNa_Completeness` (secondary)

## 10) Governance and threshold placeholders (for sign-off)

Until formal calibration is approved, use temporary triage bands:

- **Green**: completeness >= 99.5%
- **Amber**: 98.0% to <99.5%
- **Red**: <98.0%

These thresholds must be finalized in the Step 2 validation/sign-off workshop and can be regime-specific once approved.

## 11) Known caveats and interpretation notes

- Position regimes (`EMIR POS CL`, `ASIC POS CL`) intentionally have no TraNa comparison in the current logic.
- Monday logic shifts report window to cover weekend behavior (`@ReportDate1` case logic).
- Completeness is sensitive to upstream filters (`IsMifid`, `IsMifidByFCA`, settled-state, account and country exclusions).
- BI baseline is independent by design; mismatches can indicate either reporting gaps or baseline/filter drift and must be triaged.

## 12) Link back to Step 2B

Step 2C identifies **which records/regimes are incomplete**.  
Step 2B explains **which fields and derivations caused the issue**.

Operational workflow:

1. Detect issue in Step 2C output (`DailyCompleteness_AuditLog`),
2. Isolate regime/date/key mismatch,
3. Use Step 2B mapping rows and Step 2A lineage appendix to trace root cause,
4. Document resolution and control tuning.

## 13) Detailed appendix

For regulation-by-regulation implementation detail (tables, joins, and filters used per flow), see:

- `Trade_Reporting_Reconciliation_Completeness_Control_Operational_Appendix.md`
