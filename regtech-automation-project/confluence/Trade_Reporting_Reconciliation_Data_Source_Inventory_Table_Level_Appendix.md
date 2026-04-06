# Step 2A Appendix - Table-Level Inventory (Detailed)

Last updated: 2026-03-18  
Source baseline: user-provided "Trade Reporting Data Source Inventory" Confluence content

## 1) Purpose

This appendix provides the detailed table/view/feed list behind Step 2A.

Use this page together with:
- `Trade_Reporting_Reconciliation_Data_Source_Inventory_Catalog.md` (summary/source-register view)
- `Trade_Reporting_Reconciliation_Field_Mapping_Matrix.md` (field-by-field reconciliation view)

## 2) Taxonomy note used in this repository

To align with current project decisions:
- MiFID (EU/UK) is modeled as ARM-based (TRAX path).
- EMIR (EU/UK) and ASIC are modeled as TR-based (REGIS/DTCC paths by flow).

## 3) MiFID / EMIR / ASIC (direct reporting model family)

### 3.1 Operational / BI baseline sources

#### Synapse DWH
- Server: `SYNAPSE-DWH-PROD`
- Database: `sql_dp_prod_we`
- Schema: `DWH_dbo`
- Tables:
  - `Dim_Position`
  - `Dim_Instrument`
  - `Fact_SnapshotCustomer`
  - `Dim_Range`

#### Hedge execution
- Server: `AZR-W-REAL-DB-2-BIDBUser`
- Database: `etoro`
- Schema: `Hedge`
- Tables:
  - `ExecutionLog`

#### Shared reference (RegReportDB)
- Server: `AZR-WE-BI-21`
- Database: `RegReportDB`
- Tables:
  - `Reg_Instruments_SCD`
  - `Reg_LiquidtyAcount_SCD`

### 3.2 Source tables (RegReportDB)

#### EMIR source tables
- `EMIR2_Customer`
- `EMIR2_InstrumentMetaData`

#### MiFID source tables
- `FCA_DLTINS_Prev`
- `FCA_FULINS_Prev`
- `FIRDS_DLTINS_Prev`
- `FIRDS_FULINS`
- `FuturesMetaData`
- `MIFID2_Customer`
- `MIFID2_RegChange_Customer`
- `MIFID2_NPD_TRAX`
- `MIFID2_Removed_OP_Partials`
- `MIFID2_Instruments_To_Exclude`

#### ASIC source tables
- `ASIC2_Customer_PositionReport`
- `ASIC2_Daily_Prices`
- `ASIC2_InstrumentMetaData`
- `ASIC2_Instrument_Automation`
- `ASIC2_Instrument_Automation_Daily_Backup`
- `ASIC2_Positions`
- `ASIC2_Positions_SCD`
- `ASIC2_Positions_SCD_History`
- `ASIC2_Removed_OP_Partials`

#### Shared enrichment / metadata tables
- `Reg_Instruments_SCD`
- `Reg_LiquidtyAcount_SCD`
- `Reg_Metadata`
- `Reg_MigrationInOut_Population`
- `Reg_RegulationInOutDailyData`
- `Reg_Regulation_Movments_Positions`

### 3.3 External enrichment reference tables

#### ANNA DSB
- Server: `AZR-WE-BI-20`
- Database: `RTS`
- Schema: `dbo`
- Tables:
  - `UPI_Commodities`
  - `UPI_Credit`
  - `UPI_Equity`
  - `UPI_Forex`
  - `UPI_Rates`

### 3.4 Upstream transformation tables (RegReportDB)

#### EMIR ext tables
- `EMIR2_ext_Customer`
- `EMIR2_ext_DWH_V_Liabilities`
- `EMIR2_ext_Position`

#### MiFID ext tables
- `MIFID2_ext_Customer`
- `MIFID2_ext_Position`
- `MIFID2_ext_PositionChangeLog`
- `MIFID2_ext_HedgeExecutionLog`
- `MIFID2_ext_RegChange_Customer`
- `MIFID2_ext_RegChange_Position`
- `MIFID2_ext_Position_TRAX`
- `MIFID2_ext_Mirror`

#### ASIC ext tables
- `ASIC2_ext_Position`
- `ASIC2_ext_Customer`
- `ASIC2_Reg_Ext_DailyMaxPrices`
- `ASIC2_ext_DWH_V_Liabilities`
- `ASIC2_ext_OpenPositions_PositionsReport`
- `ASIC_ext_PositionChangeLog`

#### Shared ext/enrichment tables
- `Reg_Ext_T_PriceCandle60Min`
- `Reg_Ext_Trade_GetInstrument`
- `Reg_Ext_Trade_InstrumentMetaData`
- `Reg_Ext_CurrencyPriceMaxDateWithSplit`
- `Reg_Ext_CustomerLatinName`
- `Reg_Ext_DictionaryCurrency`
- `Reg_Ext_DictionaryCurrencyType`
- `Reg_Ext_HistorySplitRatio`
- `Reg_Instruments_ext`
- `Reg_Ext_HedgeEMSOrders`
- `Reg_Ext_HedgeOrderLog`
- `Reg_Ext_HistoryOrderForClose`
- `Reg_Ext_HistoryOrderForOpen`
- `Reg_Ext_History_CloseExecutionPlan`
- `Reg_Ext_History_ExecutedCloseOrders`
- `Reg_Ext_History_ExecutedOpenOrders`
- `Reg_Ext_History_OpenExecutionPlan`
- `Reg_Ext_MigrationInOut_STG`
- `Reg_Ext_DailyMaxPrices`
- `Reg_Ext_DictionaryClosePositionActionType`
- `Reg_Ext_HedgeExecutionLog`
- `Reg_Ext_HistoryPositionChangeLog`
- `Reg_Ext_LiquidityAccountID`
- `Reg_Ext_LiquidityProviders`

### 3.5 Regulatory report tables (expected state)

#### MiFID report tables
- `MIFID2_Report`
- `MIFID2_Hedge_Report`
- `MIFID2_ETORO_Report`
- `MIFID2_ME_Report`

#### EMIR report tables
- `EMIR2_Refit_Report`
- `EMIR2_Refit_Report_Daily`
- `EMIR2_Report_Refit_Collateral`
- `EMIR2_ETORO_Refit_Trades`
- `EMIR2_ETORO_Refit_Positions`
- `EMIR3_ME_Refit_Report`
- `EMIR3_UK_Refit_Report`
- `EMIR3_UK_Refit_Report_Daily`
- `EMIR3_UK_Refit_Report_Collateral`

### 3.5.1 Procedure-derived lineage (validated from `SP_EMIR3_UK_Refit_Report_Daily`)

The stored procedure provided (`dbo.SP_EMIR3_UK_Refit_Report_Daily`) confirms concrete dependencies for
`dbo.EMIR3_UK_Refit_Report_Daily`.

#### Target table written by procedure
- `dbo.EMIR3_UK_Refit_Report_Daily` (truncate + insert pattern)

#### Direct base objects referenced
- `dbo.EMIR2_Position`
- `dbo.EMIR2_Customer`
- `dbo.Reg_Instruments_SCD`
- `dbo.EMIR2_InstrumentMetaData`
- `dbo.Reg_Ext_DictionaryCurrency`
- `dbo.ISO_Currencies_Static`
- `dbo.Reg_Ext_DailyMaxPrices`
- `dbo.EMIR3_UK_Refit_Report` (previous-day state and directional backfill)
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[emir_corporate_clients_details]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_position_ids]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_instruments]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[emir_refit_taxonomy]`
- `[ThirdParty_Fivetran].[Fivetran].[regtech].[emir_refir_upi]`

#### Procedure staging chain (temporary tables)
- `#emir_UK_clients_details` (UK + REFIT-filtered client details)
- `#EMIR2_Position` (position/trade extraction for eligible clients)
- `#Metadata` (tradable instrument metadata and ISO/currency normalization)
- `#EMIR2_InstrumentMetaData` (instrument metadata with overrides and ISIN cleanup)
- `#pos_opendate` (min open date per CID/instrument)
- `#pos_openprice` (aggregated open price per CID/instrument)
- `#PricesEOD` (EOD bid/ask snapshot filtered by report date)
- `#Valid_Pos` (aggregated net position and quantity)
- `#all` (union of synthetic position records and trade records)
- `#EMIR3_UK_Report_Prev` (previous report-day UTI/confirmation/execution pull)
- `#EMIR3_UK_Refit_Report_Daily` (final shaped dataset before target insert)

### 3.5.2 Procedure-derived lineage (validated from `SP_EMIR3_UK_Refit_Report_Collateral`)

The stored procedure provided (`dbo.SP_EMIR3_UK_Refit_Report_Collateral`) confirms concrete dependencies for
`dbo.EMIR3_UK_Refit_Report_Collateral`.

#### Target table written by procedure
- `dbo.EMIR3_UK_Refit_Report_Collateral` (truncate + insert pattern)

#### Direct base objects referenced
- `dbo.EMIR2_Position`
- `dbo.EMIR2_Customer`
- `dbo.EMIR2_ext_DWH_V_Liabilities`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[emir_corporate_clients_details]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_instruments]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_position_ids]`

#### Procedure staging chain (temporary tables)
- `#emir3_UK_coll_clients_details` (UK + REFIT-filtered client details)
- `#EMIR3_collateral_ids` (eligible collateral population by CID/Regulation with exclusions)
- `#equity` (RealizedEquity/Credit/TotalPositionsAmount by CID from liabilities source)
- `#EMIR3_collateral_calculation` (counterparty type and excess calculation basis)
- `#EMIR3_collateral_calculation_agg` (aggregation by CID or LEI-based collateral portfolio code)

#### Key derived output fields validated by procedure logic
- `Counterparty_2_identifier_type` (derived from `AccountTypeID` and `PlayerLevelID`)
- `Collateral_portfolio_code` (CID/LEI-dependent derivation)
- `Variation_margin_posted_by_counterparty_1_pre_haircut`
- `Variation_margin_posted_by_counterparty_1_post_haircut`
- `Excess_collateral_posted_by_counterparty_1`
- `Collateral_timestamp`
- `Action_type` (set to `MARU`)

### 3.5.3 Procedure-derived lineage (validated from `SP_EMIR2_Refit_Report_Daily`)

The stored procedure provided (`dbo.SP_EMIR2_Refit_Report_Daily`) confirms concrete dependencies for
`dbo.EMIR2_Refit_Report_Daily` (EMIR EU REFIT daily flow).

#### Target table written by procedure
- `dbo.EMIR2_Refit_Report_Daily` (truncate + insert; plus corporate "flipped" insert)

#### Direct base objects referenced
- `dbo.EMIR2_Position`
- `dbo.EMIR2_Customer`
- `dbo.Reg_Instruments_SCD`
- `dbo.EMIR2_InstrumentMetaData`
- `dbo.Reg_Ext_DictionaryCurrency`
- `dbo.ISO_Currencies_Static`
- `dbo.Reg_Ext_DailyMaxPrices`
- `dbo.EMIR2_Refit_Report` (previous-day state and directional backfill)
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[emir_corporate_clients_details]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_instruments]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_position_ids]`
- `[ThirdParty_Fivetran].[Fivetran].[regtech].[regulation_report_excluded_cids]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[emir_refit_taxonomy]`
- `[ThirdParty_Fivetran].[Fivetran].[regtech].[emir_refir_upi]`

#### Procedure staging chain (temporary tables)
- `#EMIR2_Position` (position/trade extraction for in-scope regulations)
- `#Metadata` (tradable instrument metadata and ISO/currency normalization)
- `#EMIR2_InstrumentMetaData` (instrument metadata with overrides and ISIN cleanup)
- `#pos_opendate` (min open date per CID/instrument)
- `#pos_openprice` (aggregated open price per CID/instrument)
- `#PricesEOD` (EOD bid/ask snapshot filtered by report date)
- `#Valid_Pos` (aggregated net position and quantity)
- `#all` (union of synthetic position records and trade records)
- `#EMIR2_Report_Prev` (previous report-day UTI/ticket/confirmation/execution pull)
- `#emir_corporate_clients_details` (corporate profile enrichment and sector split logic)
- `#EMIR2_Refit_Report_Daily` (final shaped dataset before target insert)

#### Key derived output fields validated by procedure logic
- `Ticket` and `UTI` generation/fallback logic (reusing prior-day values when available)
- `Counterparty_2` and `Counterparty_2_identifier_type` derivations
- `Reporting_obligation_of_counterparty_2` (GB vs non-GB logic by account type and REFIT flags)
- `Product_classification`, `Base_product`, `Sub_product`, `Further_sub_product`
- `Valuation_amount` recalculation on insert using `#PricesEOD` and directional formula
- `Uncollateralised` flag in final insert logic
- Corporate "flipped" counterparty insert (`FlippedReport = 1`)

### 3.5.4 Procedure-derived lineage (validated from `SP_EMIR2_ETORO_Refit_Positions`)

The stored procedure provided (`dbo.SP_EMIR2_ETORO_Refit_Positions`) confirms concrete dependencies for
`dbo.EMIR2_ETORO_Refit_Positions` (ETORO positions-specific EMIR REFIT flow).

#### Target table written by procedure
- `dbo.EMIR2_ETORO_Refit_Positions` (delete-by-date loop + insert)

#### Direct base objects referenced
- `dbo.Reg_Instruments_SCD`
- `dbo.Reg_Ext_DictionaryCurrency`
- `dbo.ISO_Currencies_Static`
- `dbo.Reg_Ext_Trade_InstrumentMetaData`
- `dbo.Reg_Ext_Trade_GetInstrument`
- `dbo.ASIC_Positions_AGG`
- `dbo.ASIC_ext_OpenPositions_PositionsReport`
- `dbo.Reg_Ext_DailyMaxPrices`
- `dbo.EMIR2_ETORO_Refit_Positions` (previous-day directional backfill for `for_update` rows)
- `[ThirdParty_Fivetran].[Fivetran].[regtech].[regulation_report_excluded_cids]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_instruments]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_position_ids]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[emir_refit_taxonomy]`
- `[ThirdParty_Fivetran].[Fivetran].[regtech].[emir_refir_upi]`

#### Procedure staging chain (temporary tables)
- `#Metadata` (tradable instrument metadata and ISO/currency normalization)
- `#TB_InstrumentMetaData` (instrument metadata with ExchangeID override and ISIN cleanup)
- `#GetInstrument_abv` (buy/sell currency abbreviation normalization)
- `#RE_AGG_ASIC_Positions` (aggregated source position population from `ASIC_Positions_AGG`)
- `#EMIR2_ETORO_Refit_Positions` (final shaped dataset before insert)

#### Key derived output fields validated by procedure logic
- `Ticket` and `UTI` generated as deterministic ETORO position patterns:
  - `Ticket = 'AUSHN' + InstrumentID + Date + 'E'`
  - `UTI = reporting entity LEI + Ticket pattern`
- `Counterparty_2` fixed mapping for this flow (`549300OK2V4QF20B0D04`)
- `Product_classification`, `Base_product`, `Sub_product`, `Further_sub_product` from InstrumentID case logic
- `UPI` + taxonomy fields (`Isda_taxonomy`, `Anna_*`) via Fivetran joins
- `Valuation_amount` recalculated on final insert from aggregated EOD price delta:
  - quantity * (EOD price - open price), sign-aware by `IsBuy`
- `Uncollateralised` field derived in final insert from `Level` and counterparty list logic

### 3.5.5 Procedure-derived lineage (validated from `SP_EMIR2_ETORO_Refit_Trades`)

The stored procedure provided (`dbo.SP_EMIR2_ETORO_Refit_Trades`) confirms concrete dependencies for
`dbo.EMIR2_ETORO_Refit_Trades` (ETORO intercompany/open-trade EMIR REFIT flow).

#### Target table written by procedure
- `dbo.EMIR2_ETORO_Refit_Trades` (delete-by-date loop + insert)

#### Direct base objects referenced
- `dbo.Reg_Instruments_SCD`
- `dbo.Reg_Ext_DictionaryCurrency`
- `dbo.ISO_Currencies_Static`
- `dbo.Reg_Ext_Trade_InstrumentMetaData`
- `dbo.Reg_Ext_Trade_GetInstrument`
- `dbo.ASIC_Transactions`
- `dbo.ASIC_ext_OpenPositions_PositionsReport`
- `dbo.ASIC_Customer_PositionReport`
- `dbo.ASIC_Positions_AGG` (for earliest occurred date helper)
- `[ThirdParty_Fivetran].[Fivetran].[regtech].[regulation_report_excluded_cids]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_instruments]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_position_ids]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[emir_refit_taxonomy]`
- `[ThirdParty_Fivetran].[Fivetran].[regtech].[emir_refir_upi]`

#### Procedure staging chain (temporary tables)
- `#Metadata` (tradable instrument metadata and ISO/currency normalization)
- `#TB_InstrumentMetaData` (instrument metadata with ExchangeID override and ISIN cleanup)
- `#GetInstrument_abv` (buy/sell abbreviation normalization)
- `#MinPossitionOccured` (minimum occurred date per instrument)

#### Key derived output fields validated by procedure logic
- `Ticket` and `UTI` generated as deterministic ETORO trade/open-position patterns:
  - `Ticket = 'AUSHP' + PositionID + side/open-close suffix`
  - `UTI = reporting entity LEI + 'AUSHP' pattern`
- `Subsequent_position_UTI` linked to the ETORO positions pattern (`AUSHN...`)
- `Direction` derived from `OpenORClose` and `IsBuy`
- `Product_classification`, `Base_product`, `Sub_product`, `Further_sub_product`
- `UPI` + taxonomy fields (`Isda_taxonomy`, `Anna_*`) via Fivetran joins
- `Notional_amount_of_leg_1` derived as `OpenPrice * Quantity`
- `Valuation_amount` intentionally empty in this trade flow (trade-level TCTN record)
- `Action_type` fixed to `POSC`, `Level` fixed to `TCTN`, `Uncollateralised` empty

#### ASIC report tables
- `ASIC2_Transactions`
- `ASIC2_Transactions_Hedge`
- `ASIC2_Positions_AGG`
- `ASIC2_Positions_AGG_Hedge`
- `ASIC2_Collateral`

### 3.6 Submitted/actual ingestion tables

#### Submitted-state (planned/partial)
- Databricks catalog: `main.regtech`
- Indicative tables:
  - `bronze_cappitech_submissions`
  - `bronze_cappitech_submission_status`

#### Actual-state (REGIS active in current inventory)
- Databricks catalog: `main.regtech`
- Tables:
  - `bronze_regis_s030_trade_activity_report`
  - `bronze_regis_s091_reconciliation_report`
  - `bronze_regis_s092_rejections_report`
  - `bronze_regis_s106_warnings_report`
  - `bronze_regis_s107_trade_state_report`

Note: DTCC/TRAX response ingestion is represented as not yet complete in the source content.

## 4) CAT (US) model

### 4.1 Operational/log source tables

#### Databricks `main.general`
- `main.general.bronze_etoro_dwh_historyorderforclose`
- `main.general.bronze_etoro_dwh_historyorderforopen`
- `main.general.bronze_db_logs_history_executedopenorders`
- `main.general.bronze_db_logs_history_executionplanchangelog`
- `main.general.bronze_db_logs_history_openexecutionplan`

#### Databricks `main.bi_db`
- `main.bi_db.bronze_db_logs_history_orderforopen`
- `main.bi_db.bronze_db_logs_history_orderforclose`
- `main.bi_db.bronze_db_logs_history_executedcloseorders`
- `main.bi_db.bronze_db_logs_history_closeexecutionplan`

### 4.2 Upstream transformation tables

#### SQL Server RegReportDB
- `Reg_Ext_US_CustomerApexData`
- `Reg_Ext_US_Customers`
- `Reg_Ext_HedgeEMSOrders`
- `Reg_Ext_HedgeOrderLog`
- `Reg_Ext_HistoryOrderForClose`
- `Reg_Ext_HistoryOrderForOpen`
- `Reg_Ext_History_CloseExecutionPlan`
- `Reg_Ext_History_ExecutedCloseOrders`
- `Reg_Ext_History_ExecutedOpenOrders`
- `Reg_Ext_History_OpenExecutionPlan`

#### Databricks `main.regtech_stg`
- `reg_ext_us_customers`
- `reg_ext_us_customerapexdata`
- `reg_ext_hedgeemsorders`
- `reg_ext_hedgeorderlog`
- `reg_ext_historyorderforclose`
- `reg_ext_historyorderforopen`
- `reg_ext_history_closeexecutionplan`
- `reg_ext_history_executedcloseorders`
- `reg_ext_history_executedopenorders`
- `reg_ext_history_openexecutionplan`

### 4.3 CAT report tables (expected state)

#### SQL Server RegReportDB
- `Reg_US_COrders`
- `Reg_US_NOrders`
- `Reg_US_ROrders`
- `Reg_US_Fullfilment`
- `Reg_US_Reconsile`
- `Reg_US_Reconsile_Details`
- `Reg_US_Customers`

#### Databricks mirrors (`main.regtech`)
- `main.regtech.gold_regreportdb_prod_dbo_reg_us_corders`
- `main.regtech.gold_regreportdb_prod_dbo_reg_us_customers`
- `main.regtech.gold_regreportdb_prod_dbo_reg_us_fullfilment`
- `main.regtech.gold_regreportdb_prod_dbo_reg_us_norders`
- `main.regtech.gold_regreportdb_prod_dbo_reg_us_reconsile`
- `main.regtech.gold_regreportdb_prod_dbo_reg_us_reconsile_details`
- `main.regtech.gold_regreportdb_prod_dbo_reg_us_rorders`

### 4.4 Actual-state evidence
- SharePoint files (eToro USA):
  - `CAT Reporter Portal Event Count`
  - `CAT Reporter Portal Summary`

## 5) SFTR model

### 5.1 Source tables
- Databricks `main.general`:
  - `main.general.gold_vision_etoro`
  - `main.general.gold_visionet_r002_eod_trades_et`

### 5.2 SFTR reporting table
- Databricks `main.regtech_stg`:
  - `main.regtech_stg.bronze_sftr_report`

## 6) LTR model

### 6.1 Source tables
- `main.dealing.gold_sql_dp_prod_we_dealing_dbo_dealing_marex_recon_eodholdings_futures`
- `main.bi_output_stg.customer_radar_view_dim_customer`

### 6.2 LTR tracking / audit tables (`main.regtech_stg`)
- `main.regtech_stg.bronze_ltr_file_runs`
- `main.regtech_stg.bronze_ltr_transfers`
- `main.regtech_stg.bronze_ltr_cftc_thresholds`
- `main.regtech_stg.bronze_ltr_ocr_102a_runs`
- `main.regtech_stg.bronze_ltr_instrument_map`
- `main.regtech_stg.bronze_ltr_responses`

## 7) LP delegated model

### 7.1 Internal DUCO tables/views

#### Databricks `main.dealing`
- `main.dealing.gold_sql_dp_prod_we_dealing_dbo_v_dealing_duco_eodrecon`
- `main.dealing.gold_sql_dp_prod_we_dealing_dbo_dealing_duco_activityrecon`

#### Synapse `Dealing_dbo`
- `Dealing_Duco_EODRecon`
- `Dealing_Duco_ActivityRecon`

### 7.2 Derived reconciliation tables
- `Dealing_IGReconTrades`
- `Dealing_IGReconEODHolding`
- Additional stored-procedure-derived reconciliation tables

### 7.3 LP external source tables (`Dealing_staging`)
- `LP_EdnF_CoreTrades`
- `LP_EdnF_CorePosition`
- `LP_GSNOP_GS_ETORO_COLL_Trades`
- `LP_GS_SRPB_*`
- `LP_UBS_Todays_Trades`
- `LP_UBS_InventoryEOD`
- `LP_IG_OH_OrderHistory`
- `LP_IG_PS_EODPositions`
- `LP_SAXO_*_TradesExecuted`
- `LP_SAXO_*_OpenPositions`

### 7.4 Actual-state ingestion
- REGIS: ingested (via existing TR response pipeline)
- UNAVISTA: not fully ingested
- DTCC: not fully ingested

## 8) APA model

### 8.1 Source event tables
- Databricks `main.trading`:
  - `bronze_event_hub_prod_event_streaming_we_client_trade_evh`
- Databricks `main.dealing`:
  - `bronze_event_hub_prod_event_streaming_we_finance_tcr_evh`

### 8.2 Actual-state response table
- Databricks `main.regtech`:
  - `bronze_tradeecho_responses`

## 9) External endpoints registry (non-table systems)

These are submission/response endpoints, not internal tables:
- TRAX (ARM)
- Regis-TR (TR)
- DTCC (TR / SFTR endpoint)
- TradeEcho / LSEG (APA)
- FINRA (CAT)
- CME / CFTC (LTR)
- Cappitech / S3 vendor exchange layers

## 10) Known gaps and quality notes

- Some model flows still have partial ingestion coverage (notably non-REGIS LP and selected DTCC/TRAX paths).
- Manual spreadsheet dependencies remain and should be reduced over time.
- Shared reference integrity checks remain important where migration is partial.
- Field-level control logic and tolerances are defined in Step 2B matrix, not this appendix.
