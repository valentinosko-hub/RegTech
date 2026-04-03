# LP Delegated Reporting - Data Source Flow

```mermaid
flowchart LR
  S1["Internal execution truth\nSynapse main.dealing DUCO views\nDealing_Duco_EODRecon / ActivityRecon"]
  S2["LP source data\nSynapse Dealing_staging LP_* tables\nSaxo / UBS / IG / Marex / Goldman"]
  ST1["Stage 1 alignment\nInternal vs LP validation"]
  ST2["Stage 2 delegated reporting\nLP submits to REGIS / UNAVISTA / DTCC"]
  A["Actual state\nTR response files\nREGIS ingested / UNAVISTA & DTCC partial"]
  R["Recon controls\nAlignment + TR feedback comparison"]

  S1 --> ST1
  S2 --> ST1
  ST1 --> ST2 --> A --> R
```

