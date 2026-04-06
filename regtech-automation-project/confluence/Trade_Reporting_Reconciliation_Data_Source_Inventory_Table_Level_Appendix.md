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

### 3.5.6 Procedure-derived lineage (validated from `SP_EMIR2_Seychelles_Refit_Report_Daily`)

The stored procedure provided (`dbo.SP_EMIR2_Seychelles_Refit_Report_Daily`) confirms concrete dependencies for
`dbo.EMIR2_Seychelles_Refit_Report_Daily` (EMIR Seychelles/RegulationID 9 REFIT daily flow).

#### Target table written by procedure
- `dbo.EMIR2_Seychelles_Refit_Report_Daily` (truncate + insert pattern)

#### Direct base objects referenced
- `dbo.EMIR2_Position`
- `dbo.EMIR2_Customer`
- `dbo.Reg_Instruments_SCD`
- `dbo.EMIR2_InstrumentMetaData`
- `dbo.Reg_Ext_DictionaryCurrency`
- `dbo.ISO_Currencies_Static`
- `dbo.Reg_Ext_DailyMaxPrices`
- `dbo.EMIR2_Refit_Report` (previous-day directional backfill for zero-quantity rows)
- `[ThirdParty_Fivetran].[Fivetran].[regtech].[regulation_report_excluded_cids]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_instruments]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_position_ids]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[emir_refit_taxonomy]`
- `[ThirdParty_Fivetran].[Fivetran].[regtech].[emir_refir_upi]`

#### Procedure staging chain (temporary tables)
- `#Metadata` (tradable instrument metadata and ISO/currency normalization)
- `#EMIR2_Position` (RegulationID 9 scoped source positions/trades)
- `#EMIR2_InstrumentMetaData` (instrument metadata with exchange override and ISIN cleanup)
- `#pos_opendate` (earliest open occurrence by instrument)
- `#pos_openprice` (aggregated open price by instrument)
- `#PricesEOD` (EOD bid/ask snapshot filtered by report date)
- `#Valid_Pos` (aggregated net quantity/side by instrument)
- `#all` (union of synthetic position rows and trade rows)
- `#EMIR2_Report_Prev` (previous-day UTI/ticket/execution/confirmation pull)
- `#EMIR2_Seychelles_Refit_Report_Daily` (final shaped dataset before target insert)

#### Key derived output fields validated by procedure logic
- Scope hard-filtered to `RegulationID = 9` with fixed Seychelles counterparty values:
  - `Counterparty_2 = 549300L7LPQNKJQ1IW32`
  - `Country_of_counterparty_2 = SC`
- `Ticket` and `UTI` generation/fallback:
  - position (`Trade = 0`) rows reuse prior-day `ERP.Ticket`/`ERP.UTI` when available
  - else position pattern `HN + InstrumentID + Date + E`
  - trade (`Trade = 1`) pattern `HP + PositionID + side/open-close suffix`
- `Direction` includes `for_update` placeholder for zero-quantity rows, then backfilled from latest
  `EMIR2_Refit_Report` non-zero UTI direction history
- `Action_type`/`Level` split:
  - position rows -> `Level = PSTN`, empty `Action_type`
  - trade rows -> `Level = TCTN`, `Action_type = POSC`
- `Valuation_amount` calculated at final insert for `PSTN` rows using directional
  quantity * (EOD bid/ask - open price) logic
- `UPI` + taxonomy fields (`Isda_taxonomy`, `Anna_*`) via Fivetran joins
- `Uncollateralised` derived in final insert:
  - empty for `TCTN`
  - `TRUE` for `PSTN` when `Counterparty_2` is in configured LEI set, else `FALSE`

### 3.5.7 Procedure-derived lineage (validated from `SP_EMIR3_ME_Refit_Report`)

The stored procedure provided (`dbo.SP_EMIR3_ME_Refit_Report`) confirms concrete dependencies for
`dbo.EMIR3_ME_Refit_Report` (EMIR ME/RegulationID 11 REFIT daily flow).

#### Target table written by procedure
- `dbo.EMIR3_ME_Refit_Report` (delete-by-date loop + insert pattern)

#### Direct base objects referenced
- `dbo.EMIR2_Position`
- `dbo.EMIR2_Customer`
- `dbo.Reg_Instruments_SCD`
- `dbo.EMIR2_InstrumentMetaData`
- `dbo.Reg_Ext_DictionaryCurrency`
- `dbo.ISO_Currencies_Static`
- `dbo.Reg_Ext_DailyMaxPrices`
- `dbo.EMIR3_ME_Refit_Report` (previous-day UTI/ticket/execution/confirmation and direction backfill source)
- `[ThirdParty_Fivetran].[Fivetran].[regtech].[regulation_report_excluded_cids]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_instruments]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_position_ids]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[emir_refit_taxonomy]`
- `[ThirdParty_Fivetran].[Fivetran].[regtech].[emir_refir_upi]`

#### Procedure staging chain (temporary tables)
- `#Metadata` (tradable instrument metadata and ISO/currency normalization)
- `#EMIR2_Position` (RegulationID 11 scoped source positions/trades)
- `#EMIR2_InstrumentMetaData` (instrument metadata with exchange override and ISIN cleanup)
- `#pos_opendate` (earliest open occurrence by instrument)
- `#pos_openprice` (aggregated open price by instrument)
- `#PricesEOD` (EOD bid/ask snapshot filtered by report date)
- `#Valid_Pos` (aggregated net quantity/side by instrument)
- `#all` (union of synthetic position rows and trade rows)
- `#EMIR2_Report_Prev` (previous-day UTI/ticket/execution/confirmation pull from ME report)
- `#EMIR3_ME_Refit_Report` (final shaped dataset before target insert)

#### Key derived output fields validated by procedure logic
- Scope hard-filtered to `RegulationID = 11` with fixed ME counterparty mapping:
  - `Counterparty_2 = 254900TH30J939UL7C24`
  - `Country_of_counterparty_2` is blank in this flow
- `Ticket` and `UTI` generation/fallback:
  - position (`Trade = 0`) rows reuse prior-day `ERP.Ticket`/`ERP.UTI` when available
  - else position pattern `MEHN + InstrumentID + Date + E`
  - trade (`Trade = 1`) pattern `MEHP + PositionID + side/open-close suffix`
- `Direction` includes `for_update` placeholder for zero-quantity rows, then backfilled from latest
  `EMIR3_ME_Refit_Report` non-zero UTI direction history (ME flow side mapping differs from Seychelles)
- `Action_type`/`Level` split:
  - position rows -> `Level = PSTN`, empty `Action_type`
  - trade rows -> `Level = TCTN`, `Action_type = POSC`
- `Valuation_amount` calculated at final insert for `PSTN` rows using directional
  quantity * (EOD bid/ask - open price) logic
- `UPI` + taxonomy fields (`Isda_taxonomy`, `Anna_*`) via Fivetran joins
- `Uncollateralised` derived in final insert:
  - empty for `TCTN`
  - `TRUE` for `PSTN` when `Counterparty_2` is in configured LEI set (including ME LEI), else `FALSE`

### 3.5.8 Procedure-derived lineage (validated from `SP_EMIR2_Refit_Collateral`)

The stored procedure provided (`dbo.SP_EMIR2_Refit_Collateral`) confirms concrete dependencies for
`dbo.EMIR2_Report_Refit_Collateral` (EMIR EU collateral REFIT flow).

#### Target table written by procedure
- `dbo.EMIR2_Report_Refit_Collateral` (delete-by-date loop + insert pattern)

#### Direct base objects referenced
- `dbo.EMIR2_Position`
- `dbo.EMIR2_Customer`
- `dbo.EMIR2_ext_DWH_V_Liabilities`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[emir_corporate_clients_details]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_instruments]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_position_ids]`
- `[ThirdParty_Fivetran].[Fivetran].[regtech].[regulation_report_excluded_cids]`

#### Procedure staging chain (temporary tables)
- `#emir2_UK_coll_clients_details` (non-GB corporate clients with `refit_y_n = 'Y'`)
- `#Excluded_CIDs` (legacy CIDs with only pre-2014 activity to exclude)
- `#collateral_ids` (in-scope collateral population by CID/regulation with instrument/position exclusions)
- `#equity` (RealizedEquity/Credit/TotalPositionsAmount by CID from liabilities source)
- `#collateral_calculation` (counterparty identifier type and excess basis by account type/player level)
- `#collateral_calculation_agg` (non-corporate and corporate collateral aggregation baseline)
- `#collateral_calculation_agg2` (corporate-only aggregation keyed by LEI)

#### Key derived output fields validated by procedure logic
- Scope hard-filtered to EMIR EU regulations `RegulationID IN (1,2)` and report date.
- `Counterparty_2_identifier_type` derived from account profile:
  - `TRUE` when `AccountTypeID = 2` and `PlayerLevelID <> 4`
  - else `FALSE`
- `Collateral_portfolio_code` and counterparty mapping split by segment:
  - non-corporate uses `LEI + CID` synthetic code and reports against that code
  - corporate uses client `LEI` aggregation and dedicated corporate insert branch
- `Collateralisation_category` split:
  - non-corporate -> `PRC2`
  - corporate -> `PRC1`
- Variation/excess amounts derived from collateral aggregation:
  - non-corporate branch populates collected variation/excess fields
  - corporate branch populates posted variation/excess fields
  - `Excess` normalized to floor at zero before insert
- `Action_type` fixed to `MARU`
- `UTI` intentionally blank in collateral output (explicit TODO comment in SP)

### 3.5.9 Procedure-derived lineage (validated from `SP_ASIC2_TransactionsReport`)

The stored procedure provided (`dbo.SP_ASIC2_TransactionsReport`) confirms concrete dependencies for
`dbo.ASIC2_Transactions` (ASIC transaction-level report construction).

#### Target tables written by procedure
- `dbo.ASIC2_Transactions` (delete-by-date loop + insert from shaped temp table)
- `dbo.ASIC2_Removed_OP_Partials` (operational side table for partial-close removals)

#### Direct base objects referenced
- `dbo.ASIC2_ext_PositionChangeLog`
- `dbo.Reg_Ext_HistorySplitRatio`
- `dbo.Reg_Instruments_SCD`
- `dbo.Reg_Ext_DictionaryCurrency`
- `dbo.ISO_Currencies_Static`
- `dbo.ASIC2_InstrumentMetaData`
- `dbo.ASIC2_ext_OpenPositions_PositionsReport`
- `dbo.ASIC2_Positions`
- `dbo.ASIC2_Customer_PositionReport`
- `dbo.Reg_Ext_CustomerLatinName`
- `dbo.Reg_DWH_StaticPosition`
- `dbo.Reg_CurrencyPrice_Ext`
- `dbo.Reg_RegulationInOutDailyData`
- `dbo.Reg_Ext_CurrencyPriceMaxDateWithSplit`
- `dbo.Reg_Instruments_ext`
- `[ThirdParty_Fivetran].[Fivetran].[regtech].[emir_refir_upi]`
- `[ThirdParty_Fivetran].[Fivetran].[regtech].[regulation_report_excluded_cids]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_instruments]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_position_ids]`

#### Procedure staging chain (temporary tables)
- `#Changelog_for_Topen` (open-position changelog snapshot for same-day create events)
- `#splits` (instrument split-ratio history for quantity adjustment)
- `#Metadata` (instrument, currency, ISIN, ISO/GBX normalization)
- `#ASIC2_InstrumentMetaData` (instrument metadata with ExchangeID override + ISIN cleanup)
- `#pos`, `#prev` (current and prior-day position snapshots)
- `#cust` (normalized customer identity, LEI, account type, country)
- `#TRADE_OPEN`, `#HISTORY_OPEN`, `#HISTORY_CLOSE`, `#pop_in` (trade/lifecycle event extraction)
- `#HISTORY_OPEN_TEMP_FOR_PartialClose`, `#pop_in_TEMP_FOR_PartialClose` (partial-close operational capture)
- `#TRADES` (unioned event-level trade dataset)
- `#ConvFixPop` (non-ISO conversion-rate backfill set)
- `#ALL_Withsplit` (split-adjustment factors by position/date/instrument)
- `#Reg_CurrencyPrice_Ext_for_ASIC` (deduplicated FX conversion helper)
- `#ASIC2_LifeCycle_Position` (normalized lifecycle payload base)
- `#ASIC2_RegOutDailyData`, `#RegOut`, `#RegOutCID`, `#Pos_CID_Prev`, `#ChangeType13`, `#RealOut`,
  `#joined_pop`, `#RealEndPop` (regulation in/out and migration handling)
- `#Prices_EOD` (EOD bid/ask for migration close events)
- `#RegInNewDate_ByTRN` (reg-in filter against pre-migration trades)
- `#ASIC2_Transactions` (final shaped records before insert)

#### Key derived output fields validated by procedure logic
- `UTI` deterministic pattern:
  - `'549300OK2V4QF20B0D04' + 'P' + PositionID + side + 'A'`
- Counterparty fields (`CDE_Counterparty_2`, identifier type, name, country) derived from account profile,
  LEI presence, CID-specific overrides, and historical fallback for missing name/country.
- Notional/price fields (`CDE_Notional_amount_of_leg_1/2`, `CDE_Price`, `CDE_Price_notation`) are instrument-type
  sensitive, with ISO/GBX normalization and conversion-rate backfill for non-ISO records.
- `CDE_Quantity_unit_of_measure_Leg_1` mapped by large InstrumentID taxonomy logic
  (including DSR updates for GOLD 24/7, Iron Ore, and Rubber).
- `CDE_Other_payment_*` fields derived for close events from `NetProfit`, with payer/receiver post-update
  replacement of `for_update` placeholders by `CDE_Counterparty_2`.
- Regulation migration handling embedded through multi-branch `RegChange` logic (`0`, `1`, `3`, `4`) and
  pruning of pre-migration transactions.
- Exclusion controls applied during final dataset build:
  testing CIDs, excluded instruments, and excluded position IDs.

### 3.5.10 Procedure-derived lineage (validated from `SP_ASIC2_TransactionsReport_Hedge`)

The stored procedure provided (`dbo.SP_ASIC2_TransactionsReport_Hedge`) confirms concrete dependencies for
`dbo.ASIC2_Transactions_Hedge` (hedge mirror output built from ASIC transaction opens).

#### Target table written by procedure
- `dbo.ASIC2_Transactions_Hedge` (delete-by-date loop + insert from base ASIC transactions)

#### Direct base objects referenced
- `dbo.ASIC2_Transactions` (single upstream source for hedge records)
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_instruments]`

#### Procedure staging chain (temporary tables)
- No temporary staging tables are used in this procedure.
- Transform is a direct `INSERT ... SELECT` from `ASIC2_Transactions` with field overrides.

#### Key derived output fields validated by procedure logic
- Scope restricted to same-day open transactions only:
  - `ReportDate = @StartDate`
  - `OpenORClose = 'O'`
- Hedge-side transformation logic:
  - `Hedge_Client = 'H'`
  - `RegChange = ''`
  - `IsBuy` inverted (`0 -> 1`, `1 -> 0`)
  - `UTI` rewritten via `REPLACE(UTI, 'P', 'H')`
  - `CDE_Direction_1_Buyer_identifier_Seller_identifier` flipped (`BYER <-> SLLR`)
- Counterparty override for hedge output:
  - `CDE_Counterparty_2 = '213800GIFQMSV7HROS23'`
  - `CDE_Counterparty_2_identifier_type = 'TRUE'`
  - `Counterparty_2_name` and `Country_of_counterparty_2` forced blank.
- Instrument exclusion control applied on target table context:
  - `regtech_excluded_instruments` where `table_name = '[ASIC2_Transactions_Hedge]'`.

### 3.5.11 Procedure-derived lineage (validated from `SP_ASIC2_PositionReport`)

The stored procedure provided (`dbo.SP_ASIC2_PositionReport`) confirms concrete dependencies for
`dbo.ASIC2_Positions` (ASIC open-position valuation snapshot).

#### Target table written by procedure
- `dbo.ASIC2_Positions` (delete-by-date loop + insert pattern)

#### Direct base objects referenced
- `dbo.ASIC2_ext_OpenPositions_PositionsReport`
- `dbo.Reg_Instruments_ext`
- `dbo.ASIC2_Customer_PositionReport`
- `dbo.Reg_Instruments_SCD`
- `dbo.Reg_Ext_DictionaryCurrency`
- `dbo.ISO_Currencies_Static`
- `dbo.Reg_Ext_CurrencyPriceMaxDateWithSplit`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_instruments]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_position_ids]`

#### Procedure staging chain (temporary tables)
- `#Positions` (open-position extraction with active-at-EOD filter)
- `#Metadata` (instrument and currency normalization with ISIN and GBX/ISO flags)
- `#Prices_EOD` (same-day close valuation prices with GBX scaling adjustment)

#### Key derived output fields validated by procedure logic
- Scope restricted to unsettled open positions active at report boundary:
  - `IsSettled = 0`
  - `OpenOccurred < @EndDate`
  - `CloseOccurred > @EndDate OR CloseOccurred IS NULL`
- Position snapshot output in `ASIC2_Positions`:
  - `Deal = PositionID`
  - `Type` flipped from buy-flag (`IsBuy=0 -> Buy`, `IsBuy=1 -> Sell`)
- Valuation economics:
  - `Open Price` from `InitForexRate`
  - `Close Price` from `#Prices_EOD` using side-sensitive ask/bid
  - `ValuationDateTime` from EOD pricing timestamp
- Currency normalization behavior retained through metadata and EOD price prep:
  - GBX prices divided by 100 in `#Prices_EOD`
  - ISO currency checks anchored via `ISO_Currencies_Static`
- Exclusion controls applied at final insert:
  - `regtech_excluded_instruments` for `[ASIC2_Positions]`
  - `regtech_excluded_position_ids` for `[ASIC2_Positions]`

### 3.5.12 Procedure-derived lineage (validated from `SP_ASIC2_PositionReport_Agg`)

The stored procedure provided (`dbo.SP_ASIC2_PositionReport_Agg`) confirms concrete dependencies for
`dbo.ASIC2_Positions_AGG` (aggregated ASIC position reporting flow with SCD-driven UTI lifecycle).

#### Target tables written by procedure
- `dbo.ASIC2_Positions_AGG` (delete-by-date loop + insert from final shaped temp dataset)
- `dbo.ASIC2_Positions_SCD` (close/update/insert/open-state maintenance)
- `dbo.ASIC2_Positions_SCD_History` (daily snapshot persistence and rerun restoration source)

#### Direct base objects referenced
- `dbo.Reg_Instruments_SCD`
- `dbo.Reg_Ext_DictionaryCurrency`
- `dbo.ISO_Currencies_Static`
- `dbo.ASIC2_ext_OpenPositions_PositionsReport`
- `dbo.ASIC2_Customer_PositionReport`
- `dbo.Reg_Ext_CustomerLatinName`
- `dbo.Reg_RegulationInOutDailyData`
- `dbo.ASIC2_Daily_Prices`
- `dbo.Reg_DWH_StaticPosition`
- `dbo.Reg_Ext_DailyMaxPrices`
- `dbo.Reg_Ext_CurrencyPriceMaxDateWithSplit`
- `dbo.ASIC2_Instrument_Automation`
- `dbo.ASIC2_InstrumentMetaData`
- `dbo.ASIC2_Positions_AGG` (prior-day directional backfill by UTI)
- `dbo.ASIC2_Positions_SCD`
- `dbo.ASIC2_Positions_SCD_History`
- `dbo.ASIC_Positions_SCD` (referenced for AGGType joins in aggregation branches)
- `[ThirdParty_Fivetran].[Fivetran].[regtech].[emir_refir_upi]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[asic_2_excluded_utis]`
- `[ThirdParty_Fivetran].[Fivetran].[regtech].[regulation_report_excluded_cids]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_instruments]`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_position_ids]`

#### Procedure staging chain (temporary tables)
- `#Metadata` (instrument-level symbol/ISIN/exchange/ISO context)
- `#Positions` (open-position population with non-ISO conversion handling and signed units)
- `#ASIC_RegOutDailyData`, `#RegInNewDate_ByCID`, `#RegInNewPrices` (regulation in/out migration adjustment)
- `#ConvFixPop` (missing non-ISO conversion-rate fix path, including historic fallback)
- `#ASIC_DailyMax_Prices` and `#Prices_EOD` (valuation pricing with non-ISO + GBX adjustments)
- `#position_rn`, `#Open_Prices` (weighted-average open price selection)
- `#Temp`, `#value0`, `#valuen0`, `#last_record`, `#closed` (net-position split and close/open lifecycle sets)
- `#closed_Attributes` (latest trade attributes for aggregate payload enrichment)
- `#ASIC2_InstrumentMetaData` (instrument metadata overrides and ISIN cleanup)
- `#OLDASICTEMP` (aggregated open-population deal-level base)
- `#TEMP` (final report-shaped aggregate output before insert)

#### Key derived output fields validated by procedure logic
- Aggregation scope is based on open positions at report boundary with signed-unit netting by CID/instrument.
- SCD lifecycle management controls aggregate UTI continuity:
  - closes prior aggregates when net units go to zero,
  - inserts new aggregates for new/reopened populations,
  - snapshots daily state into `ASIC2_Positions_SCD_History`.
- Aggregate UTI/Deal generation uses date-structured patterns with switch-date logic:
  - post-switch standardized `549300...C<CID>N<InstrumentID>D<Date>A` pattern,
  - legacy fallback branch (`E02...`) retained for historical handling.
- Direction handling includes `for_update` placeholder when net quantity equals zero, then backfill from
  prior non-zero `ASIC2_Positions_AGG` UTI history.
- Valuation outputs are explicitly produced in aggregate payload:
  - `CDE_Valuation_timestamp` from valuation date + latest pricing time,
  - `CDE_Valuation_amount` as side-aware MTM delta using close/open price and USD conversion,
  - `CDE_Valuation_currency = USD`, `CDE_Valuation_method = MTMA`.
- Counterparty and collateral portfolio fields are derived with account-type/player-level/LEI logic,
  including DSR switch-date behavior and excluded-UTI override path.
- Procedure contains targeted manual UTI remediation updates for known rejected historical cases
  (DSR-8314/8331/8496/8590/8606/8670 series).

### 3.5.13 Procedure-derived lineage (validated from `SP_ASIC2_PositionReport_Agg_Hedge`)

The stored procedure provided (`dbo.SP_ASIC2_PositionReport_Agg_Hedge`) confirms concrete dependencies for
`dbo.ASIC2_Positions_AGG_Hedge` (hedge-side aggregate ASIC position output).

#### Target table written by procedure
- `dbo.ASIC2_Positions_AGG_Hedge` (delete-by-date loop + insert from aggregate source model)

#### Direct base objects referenced
- `dbo.ASIC2_Positions_AGG` (primary source for same-day aggregate positions)
- `dbo.Reg_Instruments_SCD`
- `dbo.Reg_Ext_DictionaryCurrency`
- `dbo.ISO_Currencies_Static`
- `dbo.ASIC2_InstrumentMetaData`
- `dbo.ASIC2_Positions_AGG_Hedge` (prior-day directional backfill source for zero-quantity rows)

#### Procedure staging chain (temporary tables / CTE)
- `#Metadata` (instrument symbol/exchange/ISIN/ISO context)
- `#ASIC2_InstrumentMetaData` (instrument metadata overrides and ISIN cleanup)
- `#new_direction` (net direction and quantity by instrument from base aggregate positions)
- `help_agg_table` CTE (buy/sell weighted open/close prices, notional and UTI date derivation by instrument)
- `#TEMP` (final hedge aggregate payload before insert)

#### Key derived output fields validated by procedure logic
- Scope is same-day aggregate position population (`ASIC2_Positions_AGG.ReportDate = @StartDate`) transformed
  into hedge output shape.
- Hedge identity and side transformation:
  - `Hedge_Client = 'H'`
  - `Deal = 'H_' + InstrumentID + '_' + min_uti_date`
  - `UTI = '549300OK2V4QF20B0D04HN' + InstrumentID + 'D' + uti_date + 'A'` with explicit manual override cases.
- Counterparty override is fixed for hedge flow:
  - `CDE_Counterparty_2 = 213800GIFQMSV7HROS23`
  - `CDE_Counterparty_2_identifier_type = TRUE`
  - `Counterparty_2_name` and `Country_of_counterparty_2` are blank.
- Direction and quantity handling:
  - instrument-level direction/quantity netting from `#new_direction`,
  - `for_update` placeholder when net quantity is zero, then backfilled from prior non-zero
    `ASIC2_Positions_AGG_Hedge` history by UTI.
- Valuation and economics are recalculated at aggregate hedge level:
  - side-selected weighted open/close prices (`CDE_Price_Buy/Sell`, `Close Price Buy/Sell`),
  - `CDE_Notional_amount_of_leg_1/2`, notional quantity handling with zero-quantity logic,
  - `CDE_Valuation_amount` derived as direction-aware MTM delta with USD conversion.

### 3.5.14 Procedure-derived lineage (validated from `SP_ASIC2_CollateralReport`)

The stored procedure provided (`dbo.SP_ASIC2_CollateralReport`) confirms concrete dependencies for
`dbo.ASIC2_Collateral` (ASIC collateral reporting flow).

#### Target table written by procedure
- `dbo.ASIC2_Collateral` (delete-by-date loop + insert pattern)

#### Direct base objects referenced
- `dbo.ASIC2_Positions_AGG`
- `dbo.ASIC2_Customer_PositionReport`
- `dbo.ASIC2_ext_DWH_V_Liabilities`
- `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_instruments]`

#### Procedure staging chain (temporary tables)
- `#ASIC2_collateral_ids` (in-scope CID/regulatory/counterparty set from aggregate positions + customer profile)
- `#equity2` (RealizedEquity/Credit/TotalPositionsAmount by CID)
- `#ASIC2_collateral_calculation` (counterparty identifier type derivation with account/LEI/CID rules)
- `#ASIC2_collateral_calculation_agg` (non-corporate and corporate aggregation by counterparty code)

#### Key derived output fields validated by procedure logic
- Scope restricted to same-day aggregate-position population (`ASIC2_Positions_AGG.DateID = @StartDate`) with
  exclusion control for `[ASIC2_Collateral]` instruments.
- `CDE_Counterparty_2_identifier_type` derived from account profile logic:
  - `FALSE` for account type 14,
  - `TRUE` for corporate-like accounts (`AccountTypeID=2 and PlayerLevelID<>4`), selected CID overrides,
    or LEI-populated cases.
- `Variation_margin_collateral_portfolio_code` set to `CDE_Counterparty_2` (collateral portfolio key).
- Collateral economics populated from aggregated liabilities:
  - `CDE_Variation_margin_collected_by_reporting_counterparty_pre_haircut = TotalPositionsAmount`
  - `CDE_Currency_of_variation_margin_collected = USD`
- Static collateral attributes in current SP:
  - `CDE_Collateralisation_category = PRC2`
  - `CDE_Collateral_portfolio_indicator = TRUE`
  - `Portfolio_containing_non_reported_component_indicator = FALSE`
  - `Collateral_timestamp = <StartDate>T23:59:59Z`
  - `UTI` blank, `Action_type` blank.

### 3.5.15 Procedure-derived lineage (validated from `SP_MIFID2_Report`)

The stored procedure provided (`dbo.SP_MIFID2_Report`) confirms concrete dependencies for
MiFID reporting outputs into `dbo.MIFID2_Report` and `dbo.MIFID2_ME_Report`.

#### Target tables written by procedure
- `dbo.MIFID2_Report` (delete-by-date loop + multi-flow inserts)
- `dbo.MIFID2_ME_Report` (delete-by-date loop + ME insert)
- Side table updates:
  - `dbo.MIFID2_Removed_OP_Partials` (open-tran partials removed from report population)

#### Direct base objects referenced
- Position and customer baselines:
  - `dbo.MIFID2_ext_Position`
  - `dbo.MIFID2_Customer`
  - `dbo.MIFID2_ext_RegChange_Position`
  - `dbo.MIFID2_RegChange_Customer`
- Change/mirror/split and migration dependencies:
  - `dbo.MIFID2_ext_PositionChangeLog`
  - `dbo.MIFID2_ext_Mirror`
  - `Dictionary.Ext_TradeFund`
  - `dbo.Reg_Ext_HistorySplitRatio`
  - `dbo.Reg_MigrationInOut_Population`
  - `dbo.Reg_Regulation_Movments_Positions`
- Instrument and metadata dependencies:
  - `dbo.Reg_Instruments_SCD`
  - `dbo.Reg_Instruments_Full_Description`
  - `dbo.InstrumentMetaData_SpecialChar_Conversion`
  - `dbo.Reg_Ext_Trade_InstrumentMetaData`
  - `dbo.Reg_Ext_Trade_GetInstrument`
  - `dbo.Reg_Ext_DictionaryCurrency`
  - `dbo.Reg_Ext_DictionaryCurrencyType`
  - `dbo.FuturesMetaData`
- Internal exclusion controls:
  - `dbo.MIFID2_Instruments_To_Exclude`
- Fivetran controls/enrichment:
  - `[ThirdParty_Fivetran].[Fivetran].[google_sheets].[isin_for_instrumentid_341]`
  - `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_instruments]`
  - `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_position_ids]`
  - `[ThirdParty_Fivetran].[Fivetran].[regtech].[regulation_report_excluded_cids]`

#### Procedure staging chain (temporary tables / CTE)
- Initial extraction and normalization:
  - `#changelog`, `#mirror`, `#Positions`, `#splits`, `#split`, `#trades`
  - `#InstrumentsFullDescription`, `#Reg_Instruments_SCD`,
    `#InstrumentMetaData_SpecialChar_Conversion`, `#Metadata`
  - `#Inst_341_4UK`, `#Inst_341_UK_fix`
- Partial-close handling:
  - `#PartialPop`, `#PartialPopAll`
  - `#PartialPopRegChange`, `#PartialPopAllRegChange`
- Regulation-change handling:
  - `#MifidChangeCusts`, `#RegInOutCusts`
  - `#UKtoEUtrades`, `#EUtoUKtrades`
  - `#PositionsRegChange_Temp`, `#PositionsRegChange`
  - `#splitRegChange`, `#tradesRegChange`, `#tradesFinal`
  - `#Is_EU_UK` (customer EU/UK report flags update)

#### Key derived output fields validated by procedure logic
- Jurisdiction/report routing:
  - `RegulationReportID = 1` for EU/CySEC population,
  - `RegulationReportID = 2` for UK/FCA population,
  - plus additional inserts for Seychelles (`OrigRegulationID=9`) and ME (`OrigRegulationID=11`).
- Trade/reference identity:
  - `TransactionReferenceNumber` from `PositionIDOut` with jurisdiction-specific formatting
    (UK token removal, `SC` and `ME` suffix patterns for dedicated flows).
- Reg-change lineage:
  - `OrigRegulationID` and `RegChange` are explicitly derived from migration windows
    (`RegChange=0/1/2`), including EU<->UK moves and MIFID->other transitions.
- Price/quantity normalization:
  - split-adjusted open quantities from `Reg_Ext_HistorySplitRatio`,
  - GBX normalization (`InitForexRate`, `EndForexRate` divided by 100 when `IsGBX=1`).
- Counterparty and decision-maker population:
  - buyer/seller identifier code and type branch logic from `IDType`, `PIN_LEI`, `PIN_Type`,
    `BuyORSell`, `MirrorID`, and fund profile.
- Instrument classification and underlying mapping:
  - `InstrumentClassification`, `UnderlyingInstrumentCode`, `UnderlyingIndexName`,
    and 341 UK ISIN override from Fivetran mapping.
- Scope controls:
  - internal and external exclusion filters (`MIFID2_Instruments_To_Exclude`,
    `regtech_excluded_instruments`, `regtech_excluded_position_ids`,
    and UK excluded CIDs).

### 3.5.16 Procedure-derived lineage (validated from `SP_MIFID2_ETORO_Report`)

The stored procedure provided (`dbo.SP_MIFID2_ETORO_Report`) confirms concrete dependencies for
the MiFID EU AUS flow into `dbo.MIFID2_ETORO_Report`.

#### Target table written by procedure
- `dbo.MIFID2_ETORO_Report` (delete-by-date loop + insert for same-day AUS population)

#### Direct base objects referenced
- Source transactional population:
  - `dbo.ASIC_Transactions`
- Instrument and metadata dependencies:
  - `dbo.Reg_Instruments_SCD`
  - `dbo.Reg_Instruments_Full_Description`
  - `dbo.InstrumentMetaData_SpecialChar_Conversion`
  - `dbo.Reg_Ext_DictionaryCurrency`
  - `dbo.Reg_Ext_DictionaryCurrencyType`
- Fivetran controls:
  - `[ThirdParty_Fivetran].[Fivetran].[regtech].[regulation_report_excluded_cids]`
  - `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_instruments]`
  - `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_position_ids]`

#### Procedure staging chain (temporary tables)
- `#InstrumentsFullDescription` (latest index-name descriptions per instrument)
- `#Reg_Instruments_SCD` (tradable, date-valid SCD slice at report date)
- `#Metadata` (instrument type/currency/ISIN/MiFID flags/full name/GBX normalization context)

#### Key derived output fields validated by procedure logic
- Jurisdiction routing is fixed for this flow:
  - `RegulationReportID = 1` (MiFID EU report channel),
  - `RegulationID = 1` (EU).
- Trade/reference identity:
  - `TransactionReferenceNumber = CAST(PositionID) + OpenORClose + 'AUS' + DateID`
    (AUS-specific pattern to avoid collisions with other MiFID flows).
- Counterparty role and LEI assignment:
  - buyer/seller LEIs are hardcoded by side between EU reporting LEI (`213800GIFQMSV7HROS23`)
    and ASIC legal entity LEI (`549300OK2V4QF20B0D04`).
- Timestamp and economics:
  - `TradingDateTime` from `ASIC_Transactions.OpenTime` in UTC string format,
  - `Quantity` from `Volume`, `Price` from `OpenPrice`,
  - `PriceType` from instrument currency type (`BSPS` for type 4 else `MNTR`).
- Instrument classification and naming:
  - `InstrumentClassification` via explicit `InstrumentTypeID` + InstrumentID mapping branches,
  - `InstrumentFullName` uses `LEFT(..., 50) + ' CFD'` truncation safeguard.
- Scope controls:
  - same-day filter (`ReportDate = @StartDate`) plus Fivetran-based exclusions for CID,
    instrument, and position IDs.

### 3.5.17 Procedure-derived lineage (validated from `SP_MIFID2_HedgeEU_Report`)

The stored procedure provided (`dbo.SP_MIFID2_HedgeEU_Report`) confirms concrete dependencies for
MiFID EU hedge reporting inserts into `dbo.MIFID2_Hedge_Report` (`RegulationReportID=1`).

#### Target table written by procedure
- `dbo.MIFID2_Hedge_Report` (delete-by-date loop scoped to `RegulationReportID=1` + EU inserts)

#### Direct base objects referenced
- Hedge execution and LP identity:
  - `dbo.MIFID2_ext_HedgeExecutionLog`
  - `dbo.Reg_Ext_LiquidityAccountID`
  - `dbo.Reg_LiquidtyAcount_SCD`
- Instrument and metadata dependencies:
  - `dbo.Reg_Instruments_SCD`
  - `dbo.Reg_Instruments_Full_Description`
  - `dbo.InstrumentMetaData_SpecialChar_Conversion`
  - `dbo.Reg_Ext_DictionaryCurrency`
  - `dbo.Reg_Ext_DictionaryCurrencyType`
- Synapse + mapping enrichment for futures metadata:
  - `[SYNAPSE-DWH-PROD].[sql_dp_prod_we].[Dealing_staging].[LP_EdnF_CoreTrades]`
  - `[SYNAPSE-DWH-PROD].[sql_dp_prod_we].[Dealing_staging].[LP_IB_U1059976_Open_Positions_All]`
  - `[ThirdParty_Fivetran].[Fivetran].[google_sheets].[ed_n_f_to_istrumentid_etoro]`
- Fivetran controls:
  - `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_instruments]`
  - `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_position_ids]`

#### Procedure staging chain (temporary tables / CTE)
- Hedge execution extraction and routing:
  - `#EUtrades` (execution log extraction, LP joins, flow routing `EU/UK`, row-id sequencing)
- Instrument/metadata staging:
  - `#InstrumentsFullDescriptionEU`
  - `#Reg_Instruments_SCD`
  - `#InstrumentMetaData_SpecialChar_Conversion` (deduped by instrument/report date)
  - `#Metadata`
- ED&F / IB enrichment:
  - `#LP_EdnF_Trades_NonVIX`, `#LP_EdnF_Trades_VIX`, `#LP_EdnF_Trades`
  - `#LP_IB_Trades`
- Additional EU-via-UK hedge branch:
  - `#realstock_EUtrades_via_UK`

#### Key derived output fields validated by procedure logic
- Routing and scope:
  - output constrained to `MIFID2_Hedge_Report` with `RegulationReportID=1`,
  - primary EU branch (`rowSource='EU'`) plus EU reporting of real-stock trades routed via UK LP (`rowSource='EU-UK'`).
- Hedge transaction identity:
  - `TransactionReferenceNumber` built from normalized `ProviderExecID` + `RowID` + report date,
    with fallback to `LiquidityProvider + date + RowID`.
- Counterparty/LEI population:
  - executing entity fixed to EU LEI (`213800GIFQMSV7HROS23`) for EU branch,
    with buyer/seller LEI assigned by side and LP LEI in hedge pairing logic.
- Price and quantity controls:
  - `Quantity` from hedge `Units`,
  - `Price` from `ExecutionRate` with GBX divide-by-100 handling,
  - `PriceType` from instrument currency type (`BSPS` for type 4 else `MNTR`).
- Instrument/futures enrichment:
  - extensive `InstrumentClassification` branch logic by LP LEI/account and instrument groups,
  - ED&F/IB-driven fields for `InstrumentFullName`, `NotionalCurrency1`, `PriceMultiplier`,
    `ExpiryDate`, and `DeliveryType` for real futures scenarios.
- Control fields:
  - `ShortSellingIndicator` set to `SELL` for real stock/ETF short cases,
  - `CommodityDerivativeIndicator` set to `false` for instrument type 2,
  - `BackReportingIndicator=0`,
  - `EMSOrderID` explicitly populated in output.
- Exclusion controls:
  - instrument and position filters via Fivetran exclusion tables for `[MIFID2_Hedge_Report]`.

### 3.5.18 Procedure-derived lineage (validated from `SP_MIFID2_HedgeUK_Report`)

The stored procedure provided (`dbo.SP_MIFID2_HedgeUK_Report`) confirms concrete dependencies for
MiFID UK hedge reporting inserts into `dbo.MIFID2_Hedge_Report` (`RegulationReportID=2`).

#### Target table written by procedure
- `dbo.MIFID2_Hedge_Report` (delete-by-date loop scoped to `RegulationReportID=2` + UK insert)

#### Direct base objects referenced
- Hedge execution and LP identity:
  - `dbo.Reg_Ext_HedgeExecutionLog`
  - `dbo.Reg_Ext_LiquidityAccountID`
  - `dbo.Reg_LiquidtyAcount_SCD`
  - `dbo.Reg_Ext_HedgeHBCOrderLog` (HBC/CBH hedging type flag)
- Instrument and metadata dependencies:
  - `dbo.Reg_Instruments_SCD`
  - `dbo.InstrumentMetaData_SpecialChar_Conversion`
  - `dbo.Reg_Ext_DictionaryCurrency`
  - `dbo.Reg_Ext_DictionaryCurrencyType`
- Fivetran controls:
  - `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_instruments]`
  - `[ThirdParty_Fivetran].[Fivetran].[regulation].[regtech_excluded_position_ids]`

#### Procedure staging chain (temporary tables)
- `#UKtrades` (hedge executions for UK entity, LP joins, HBC/CBH tagging, row-id sequencing)
- `#Reg_Instruments_SCD` (date-valid tradable SCD slice)
- `#Metadata` (instrument/currency/ISIN/FCA MiFID flags/full name context)

#### Key derived output fields validated by procedure logic
- Routing and scope:
  - output constrained to `MIFID2_Hedge_Report` with `RegulationReportID=2`,
  - `rowSource='UK'`.
- Hedge transaction identity:
  - `TransactionReferenceNumber` built from normalized `ProviderExecID` + `RowID` + report date,
    with fallback to `LiquidityProvider + date + RowID`.
- Counterparty/LEI population:
  - executing entity fixed to UK LEI (`213800FLAB1OVA8OHT72`),
  - buyer/seller LEI assignment by side vs LP LEI.
- Price and quantity controls:
  - `Quantity` from hedge `Units`,
  - `Price` from `ExecutionRate` with GBX divide-by-100 handling and `numeric(16,8)` casting,
  - `PriceType` from instrument currency type (`BSPS` for type 4 else `MNTR`).
- Instrument and execution attributes:
  - FCA MiFID eligibility via `IsMifidByFCA=1`,
  - `TradingCapacity='MTCH'`,
  - `InstrumentIdentificationCode=ISINCode`,
  - `UnderlyingInstrumentCode` populated for non-real rows (`IsReal=0`).
- Control fields:
  - `CommodityDerivativeIndicator` set to `false` for instrument type 2,
  - `ExecutionWithinFirmType='ALG'`, `ExecutionWithinFirm='ETORODEALING01'`,
  - `BackReportingIndicator=0`,
  - `EMSOrderID` explicitly populated in output.
- Exclusion controls:
  - instrument and position filters via Fivetran exclusion tables for `[MIFID2_Hedge_Report]`.

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
