# Reporting Model Data Source Flows

This page provides separate flow diagrams for each reporting model, with MiFID, EMIR, and ASIC split individually.

## MiFID (EU/UK) - ARM-Based

```mermaid
flowchart LR
  A["Internal sources<br/>Synapse DWH: Dim_Position, Dim_Instrument, Fact_SnapshotCustomer<br/>Hedge: etoro.Hedge.ExecutionLog"]
  B["MiFID source tables (RegReportDB)<br/>FCA_DLTINS_Prev, FCA_FULINS_Prev, FIRDS_DLTINS_Prev, FIRDS_FULINS<br/>FuturesMetaData, MIFID2_Customer, MIFID2_RegChange_Customer<br/>MIFID2_NPD_TRAX, MIFID2_Removed_OP_Partials, MIFID2_Instruments_To_Exclude"]
  C["Upstream ext tables (RegReportDB)<br/>MIFID2_ext_Customer, MIFID2_ext_Position, MIFID2_ext_PositionChangeLog<br/>MIFID2_ext_HedgeExecutionLog, MIFID2_ext_RegChange_* , MIFID2_ext_Position_TRAX"]
  D["Expected (Golden Source)<br/>MIFID2_Report, MIFID2_Hedge_Report, MIFID2_ETORO_Report, MIFID2_ME_Report"]
  E["Submitted state<br/>Cappitech files -> TRAX (MiFID ARM)"]
  F["Actual state<br/>ARM responses (TRAX validation and acknowledgements)"]
  G["Databricks recon<br/>Bronze -> Silver -> Gold -> Reconciliation"]

  A --> B --> C --> D --> E --> F --> G
```

## EMIR (EU/UK) - TR-Based

```mermaid
flowchart LR
  A["Internal sources<br/>Synapse DWH + Hedge execution + shared reference tables"]
  B["EMIR source tables (RegReportDB)<br/>EMIR2_Customer, EMIR2_InstrumentMetaData<br/>Reg_Instruments_SCD, Reg_LiquidtyAcount_SCD"]
  C["Upstream ext tables (RegReportDB)<br/>EMIR2_ext_Customer, EMIR2_ext_Position, EMIR2_ext_DWH_V_Liabilities<br/>EMIR_Refit_UPI and shared Reg_Ext_* enrichment"]
  D["Expected (Golden Source)<br/>EMIR2_Refit_Report, EMIR2_Refit_Report_Daily, EMIR2_Report_Refit_Collateral<br/>EMIR2_ETORO_Refit_Trades, EMIR2_ETORO_Refit_Positions, EMIR3_UK_*"]
  E["Submitted state<br/>Cappitech files -> REGIS / DTCC"]
  F["Actual state<br/>TR responses: S030/S091/S092/S106/S107 (REGIS)<br/>DTCC ingestion currently partial/pending"]
  G["Databricks recon<br/>main.regtech_stg/main.regtech Bronze -> Silver -> Gold -> Reconciliation"]

  A --> B --> C --> D --> E --> F --> G
```

## ASIC - TR-Based

```mermaid
flowchart LR
  A["Internal sources<br/>Synapse positions/trades + customer/instrument enrichment"]
  B["ASIC source tables (RegReportDB)<br/>ASIC2_Customer_PositionReport, ASIC2_Daily_Prices, ASIC2_InstrumentMetaData<br/>ASIC2_Instrument_Automation*, ASIC2_Positions*, ASIC2_Removed_OP_Partials"]
  C["Upstream ext tables (RegReportDB)<br/>ASIC2_ext_Position, ASIC2_ext_Customer, ASIC2_Reg_Ext_DailyMaxPrices<br/>ASIC2_ext_DWH_V_Liabilities, ASIC2_ext_OpenPositions_PositionsReport, ASIC_ext_PositionChangeLog"]
  D["Expected (Golden Source)<br/>ASIC2_Transactions, ASIC2_Transactions_Hedge, ASIC2_Positions_AGG, ASIC2_Positions_AGG_Hedge, ASIC2_Collateral"]
  E["Submitted state<br/>Cappitech vendor path"]
  F["Actual state<br/>TR response files"]
  G["Databricks recon<br/>Expected vs Submitted vs Actual validation"]

  A --> B --> C --> D --> E --> F --> G
```

## CAT (US) - Event-Driven

```mermaid
flowchart LR
  A["Operational/log sources (Databricks)<br/>main.general.bronze_etoro_dwh_historyorderfor*<br/>main.general.bronze_db_logs_history_*<br/>main.bi_db.bronze_db_logs_history_*"]
  B["Upstream transformation<br/>SQL Reg_Ext_US_* + Databricks main.regtech_stg.reg_ext_us_*<br/>reg_ext_history_* and hedge order tables"]
  C["Expected (Golden Source)<br/>Reg_US_COrders, Reg_US_NOrders, Reg_US_ROrders, Reg_US_Fullfilment<br/>Reg_US_Reconsile, Reg_US_Reconsile_Details, Reg_US_Customers"]
  D["Submitted state<br/>S3 vendor exchange -> FINRA CAT"]
  E["Actual state<br/>CAT feedback files in eToro USA SharePoint"]
  F["Databricks recon<br/>gold_regreportdb_prod_dbo_reg_us_* mirrors + reconciliation layer"]

  A --> B --> C --> D --> E --> F
```

## SFTR - Direct to DTCC

```mermaid
flowchart LR
  A["Source data (Databricks main.general)<br/>gold_vision_etoro<br/>gold_visionet_r002_eod_trades_et"]
  B["SFTR preparation<br/>Lifecycle derivation from snapshots: NEWT, MODI, VALU, ETRM"]
  C["Expected dataset<br/>main.regtech_stg.bronze_sftr_report"]
  D["Submitted state<br/>Daily SFTR XML -> DTCC SFTP (no vendor)"]
  E["Actual state<br/>DTCC acknowledgements/rejections/validation feedback"]
  F["Databricks recon<br/>Bronze -> Silver -> Gold -> lifecycle/valuation checks"]

  A --> B --> C --> D --> E --> F
```

## LTR - Manual / Transitional

```mermaid
flowchart LR
  A["Source data<br/>main.dealing...dealing_marex_recon_eodholdings_futures<br/>main.bi_output_stg.customer_radar_view_dim_customer"]
  B["Aggregation and threshold logic<br/>CFTC threshold rules + reportable account detection"]
  C["Expected datasets<br/>LTR position file + Form 102A payload"]
  D["Submitted state<br/>FIPS-enabled VM -> CME/CFTC SFTP"]
  E["Actual state (limited)<br/>Acknowledgements + delivery tracking (no full TR-style lifecycle feedback)"]
  F["Tracking/recon tables (main.regtech_stg)<br/>bronze_ltr_file_runs, bronze_ltr_transfers, bronze_ltr_responses<br/>bronze_ltr_ocr_102a_runs, bronze_ltr_instrument_map, bronze_ltr_cftc_thresholds"]

  A --> B --> C --> D --> E --> F
```

## LP Delegated Reporting

```mermaid
flowchart LR
  A["Internal execution sources<br/>main.dealing...v_dealing_duco_eodrecon<br/>main.dealing...dealing_duco_activityrecon<br/>Synapse Dealing_Duco_EODRecon / ActivityRecon"]
  B["LP external source tables (Synapse Dealing_staging)<br/>LP_EdnF_*, LP_GSNOP_*, LP_UBS_*, LP_IG_*, LP_SAXO_*"]
  C["Stage 1 control<br/>Internal DUCO vs LP data alignment"]
  D["Submitted state (delegated)<br/>LP reports to REGIS / UNAVISTA / DTCC"]
  E["Actual state<br/>TR responses: REGIS ingested, UNAVISTA/DTCC pending"]
  F["Reconciliation coverage<br/>REGIS full; UNAVISTA/DTCC partial until ingestion is complete"]

  A --> C
  B --> C --> D --> E --> F
```

## APA (MiFID) - Real-Time Publication

```mermaid
flowchart LR
  A["Event sources<br/>main.trading.bronze_event_hub_prod_event_streaming_we_client_trade_evh<br/>main.dealing.bronze_event_hub_prod_event_streaming_we_finance_tcr_evh"]
  B["Internal event-processing services<br/>Trade events normalized for APA publication"]
  C["Submitted state<br/>APA Event Hub -> TradeEcho (LSEG)"]
  D["Actual state<br/>TradeEcho SFTP responses (/Outgoing/SRR)"]
  E["Databricks ingestion/recon<br/>main.regtech.bronze_tradeecho_responses -> recon layer"]

  A --> B --> C --> D --> E
```

