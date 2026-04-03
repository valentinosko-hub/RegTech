# Reporting Model: SFTR (Direct to DTCC) - Data Sources

```mermaid
flowchart LR
  S1["Databricks main.general<br/>gold_vision_etoro / vision EOD snapshots"]
  S2["Internal SFTR lifecycle derivation<br/>main.regtech_stg.bronze_sftr_report"]
  EXP["Expected dataset<br/>SFTR lifecycle events (NEWT/MODI/VALU/ETRM)"]
  SUB["Submitted state<br/>SFTR XML direct to DTCC SFTP (no vendor)"]
  ACT["Actual state<br/>DTCC acknowledgements / rejections / validation feedback"]
  RECON["Recon controls<br/>UTI matching + lifecycle + valuation consistency"]

  S1 --> S2 --> EXP --> SUB --> ACT --> RECON
```

