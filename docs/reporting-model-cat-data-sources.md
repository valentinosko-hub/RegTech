# CAT (US) Reporting Model - Data Source Flow

```mermaid
flowchart LR
  O["Operational/Log Sources\nmain.general + main.bi_db\nhistoryorder*, executionplan*, executed*"]
  U["Upstream Transform\nReg_Ext_US_* and order lifecycle transforms\nSQL: AZR-WE-BI-21 RegReportDB\nDBX: main.regtech_stg reg_ext_*"]
  E["Expected Dataset\nReg_US_* (SQL) + main.regtech gold mirrors"]
  S["Submitted State\nS3 vendor exchange -> FINRA CAT"]
  A["Actual State\nCAT feedback files (SharePoint eToro USA)"]
  R["Reconciliation Focus\nEvent sequencing + lifecycle completeness\n(no UTI model)"]

  O --> U --> E --> S --> A --> R
```

