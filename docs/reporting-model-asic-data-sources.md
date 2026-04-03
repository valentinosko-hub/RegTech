# ASIC Reporting Model - Data Source Flow

```mermaid
flowchart LR
  A1["Operational source of truth<br/>Synapse DWH + Hedge execution logs"] --> A2["RegReportDB source tables (ASIC)<br/>ASIC2_Positions / ASIC2_InstrumentMetaData / ASIC2_Daily_Prices"]
  A2 --> A3["Upstream ext_ transforms (RegReportDB)<br/>ASIC2_ext_Position / ASIC2_ext_Customer / liabilities / open positions"]
  A3 --> A4["Expected reporting baseline<br/>ASIC2_Transactions / ASIC2_Positions_AGG / ASIC2_Collateral"]
  A4 --> A5["Submitted state<br/>Cappitech vendor files -> ARM/TR endpoints"]
  A5 --> A6["Actual state responses<br/>TRAX / TR response files (where ingested)"]
  A6 --> A7["Databricks reconcile path<br/>Bronze -> Silver -> Gold -> Recon Engine"]
```

