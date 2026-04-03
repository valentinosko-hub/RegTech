# MiFID (EU/UK) Reporting Model - Data Sources

```mermaid
flowchart LR
  S1["Synapse DWH (SYNAPSE-DWH-PROD)<br/>Dim_Position / Dim_Instrument / Fact_SnapshotCustomer"]
  S2["Hedge execution logs<br/>AZR-W-REAL-DB-2-BIDBUser / etoro.Hedge.ExecutionLog"]
  S3["RegReportDB source + ext tables<br/>MIFID2_* / MIFID2_ext_*"]
  S4["Reference data<br/>FIRDS/FCA files + ANNA DSB (RTS) + Reg_Instruments_SCD"]

  EXP["Expected (Golden Source)<br/>RegReportDB MIFID2 report tables"]
  SUB["Submitted state<br/>Cappitech -> TRAX/ARM channels"]
  ACT["Actual state<br/>TR/ARM response files (REGIS/TRAX/DTCC where available)"]

  S1 --> EXP
  S2 --> EXP
  S3 --> EXP
  S4 --> EXP
  EXP --> SUB --> ACT
```

