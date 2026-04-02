# Trade Recon Architecture V2 (Converted from draw.io XML)

```mermaid
flowchart TB
  %% Source systems
  subgraph SW1["Source Systems"]
    direction LR
    S1["Synapse (SYNAPSE-DWH-PROD)"]
    S2["SQL Server (AZR-WE-BI-21)<br/>RegReportDB"]
    S3["SQL Server (AZR-WE-BI-21)<br/>Dealing DB"]
    S4["SQL Server (AZR-W-REAL-DB-2)<br/>Hedge (ExecutionLog)"]
    S5["Databricks (main.general)<br/>Vision / SFTR"]
    S6["Synapse (Dealing_staging)<br/>LP Tables (Trades / Positions / EOD)"]
  end

  REGEXT["Upstream / RegExt Layer<br/>SQL Server (AZR-WE-BI-21)"]
  REPORT["Regulatory Reporting (Golden Source)<br/>SQL Server (AZR-WE-BI-21 - RegReportDB)<br/>Output: Audit Tables (Expected State)"]
  SUB["Submission Layer<br/>Cappitech / APA (TradeEcho / LSEG) / TR (Regis / DTCC)<br/>Report Delivery"]

  %% Databricks platform
  subgraph DB["Databricks Platform"]
    direction LR
    BRONZE["Bronze Layer (main.regtech_stg)<br/>SFTP (REGIS / DTCC) / EventHub (APA) / Files (SFTR)"]
    SILVER["Silver Layer (main.regtech)<br/>ESMA / FCA Enrichment"]
    GOLD["Gold Layer (main.regtech / dealing)<br/>Curated / Replication<br/>Regulatory replication (CAT / ASIC SCD)"]
  end

  LP["LP Data (Execution Reality)<br/>Synapse (Dealing_staging)<br/>- Trades<br/>- Positions (EOD)<br/>- Exposure"]
  TR["TR Responses (Actual State)<br/>Databricks (main.regtech)<br/>- Regis-TR<br/>- DTCC<br/>- LSEG<br/>- TradeEcho"]
  RECON["Reconciliation Engine (Databricks)<br/>3-Way Matching: Expected / Actual / Execution<br/>Matching keys: UTI / TradeID / LEI<br/>Validation: Completeness / Field accuracy / Lifecycle"]
  OUT["Outputs / Monitoring<br/>Power BI Dashboards / Exceptions / Audit Logs"]

  LEGEND["Legend:<br/>Blue = Internal Systems<br/>Green = Databricks<br/>Purple = Vendors"]
  NOTE["Detailed table-level mapping available in:<br/>Trade Reporting Data Source Inventory"]

  %% Edges translated from XML
  SW1 --> REGEXT
  REGEXT --> REPORT
  REPORT -- "(Report Delivery)" --> SUB
  SUB --> BRONZE
  BRONZE --> SILVER --> GOLD
  GOLD -- "Expected" --> RECON
  LP -- "Execution" --> RECON
  TR -- "Actual" --> RECON
  RECON --> OUT
  REPORT -- "Expected (SQL)" --> RECON
  GOLD --> TR

  classDef internal fill:#dae8fc,stroke:#6c8ebf,color:#0e2a47;
  classDef sql fill:#ffe6cc,stroke:#bf7f3f,color:#4a2a12;
  classDef vendor fill:#e6e0f8,stroke:#7f70bf,color:#2f1a5f;
  classDef dbx fill:#d5e8d4,stroke:#6aa84f,color:#12391f;
  classDef recon fill:#f8cecc,stroke:#b8544a,color:#4a1212;
  classDef neutral fill:#ffffff,stroke:#cccccc,color:#222;

  class SW1,S1,S2,S3,S4,S5,S6,LP,TR internal;
  class REGEXT,REPORT sql;
  class SUB vendor;
  class DB,BRONZE,SILVER,GOLD dbx;
  class RECON recon;
  class OUT,LEGEND,NOTE neutral;
```
