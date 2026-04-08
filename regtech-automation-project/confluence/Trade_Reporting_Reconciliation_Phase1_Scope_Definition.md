# Phase 1 - Regulatory Scope Definition (Requirements Baseline)

Last updated: 2026-03-18  
Related epic: REG-3283 (Trade Reporting Recon - Requirements and Scope Definition)  
Owner: Valentinos Konstantinou

## 1) Purpose

Define the formal regulatory perimeter for the Trade Reporting Reconciliation Automation initiative before detailed field mapping and technical design.

This page captures:
- regulations in scope,
- reporting objects and submission models,
- high-level reconciliation objective by regime,
- business ownership.

## 2) Regulatory regimes in scope

| Regulation | Jurisdiction | Reporting object | Submission model/channel | Primary internal source domains | Reconciliation objective focus | Regulatory owner |
|---|---|---|---|---|---|---|
| MiFID II | EU (CySEC) | Trade transactions | Cappitech -> TRAX (ARM) | Trading, RegReportDB, Synapse completeness baseline | Completeness, field-level accuracy, timeliness, ARM acceptance | Ops + Compliance |
| MiFID II | UK (FCA) | Trade transactions | Cappitech -> TRAX (ARM) | Trading, RegReportDB, Synapse completeness baseline | Completeness, field-level accuracy, timeliness, ARM acceptance | Ops + Compliance |
| EMIR | EU | Position, lifecycle, valuation, collateral | Cappitech -> Regis-TR (TR) | Trading/positions, RegReportDB EMIR, reference enrichment | Completeness, lifecycle consistency, valuation/collateral alignment, TR acceptance | Ops + Compliance |
| EMIR | UK | Position, lifecycle, valuation, collateral | Cappitech -> Regis-TR (TR) | Trading/positions, RegReportDB EMIR, reference enrichment | Completeness, lifecycle consistency, valuation/collateral alignment, TR acceptance | Ops + Compliance |
| ASIC | Australia | Transactions + position/lifecycle/valuation/collateral | Cappitech -> DTCC (TR) | Trading/positions, RegReportDB ASIC, reference enrichment | Completeness, lifecycle consistency, TR acceptance | Ops + Compliance |
| CAT | US | Order and event lifecycle | S3 exchange -> FINRA CAT | Operational event logs, Reg_US outputs | Event completeness, sequence consistency, timeliness, CAT acceptance | Ops + Compliance |
| SFTR | EU | Position and lifecycle | Direct DTCC submission | Vision snapshots + derived lifecycle layers | Lifecycle completeness, valuation alignment, timeliness, DTCC acceptance | Ops + Compliance |
| LTR | US | EOD positions + account ownership / 102A payload context | FIPS VM -> CME/CFTC | Dealing futures holdings, customer ownership, threshold controls | Completeness, threshold logic integrity, submission timeliness | Ops + Compliance |
| APA | EU | Trade publication events | APA Event Hub -> TradeEcho (LSEG) | Trading events + event-processing services | Publication timeliness, completeness vs filtered MiFID baselines, acknowledgement tracking | Ops + Compliance |

## 3) Reporting granularity classification

### 3.1 Transaction-level
- MiFID II (EU/UK)

### 3.2 Event-level
- CAT
- APA (publication event stream)

### 3.3 Position and lifecycle-level
- EMIR (EU/UK)
- ASIC
- SFTR
- LTR (position/account-ownership and threshold logic)

## 4) Scope boundary (Phase 1 only)

In scope:
- definition of regulatory perimeter,
- high-level reconciliation intent by regime,
- ownership and accountability at business level.

Out of scope:
- detailed field mapping and transformation rules,
- tolerance implementation details,
- technical architecture implementation,
- exception workflow automation,
- real-time control implementation details.

## 5) Acceptance criteria checklist

- [x] List of regulations in scope documented
- [x] Reporting object and submission model defined per regulation
- [x] Reconciliation objective focus stated per regulation
- [x] Business owner model identified (Ops + Compliance)
- [x] Scope boundary and exclusions explicitly documented
