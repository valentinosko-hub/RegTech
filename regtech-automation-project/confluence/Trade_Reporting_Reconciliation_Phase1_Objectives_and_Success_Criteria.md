# Phase 1 - Reconciliation Objectives and Success Criteria

Last updated: 2026-03-18  
Related epic: REG-3283  
Related story: Define Reconciliation Objectives and Success Criteria  
Owner: Valentinos Konstantinou

## 1) Purpose

Define what "reconciled" means across reporting regimes before field-level mapping and implementation.

This page is the requirements baseline for:
- control dimensions,
- measurement intent,
- tolerance principles,
- SLA/timeliness assumptions.

## 2) End-to-end reporting chain in scope

1. Trading/dealing systems
2. Back-office and operational control layers
3. Regulatory staging and reporting tables
4. Vendor submission channels (Cappitech/S3/TradeEcho/direct)
5. Vendor acknowledgements and regulator responses (TR/ARM/CAT/APA endpoints)

## 3) Core control dimensions

| Control dimension | Objective | Measurement intent | Baseline principle |
|---|---|---|---|
| Completeness | Report all required records | Internal reportable population vs submitted/acknowledged population | Population variance <= 1% unless model-specific override |
| Accuracy | Preserve field-level integrity | Source fields vs reporting fields vs response evidence | Tolerance model by field class (exact-match vs numeric tolerance) |
| Timeliness | Meet regulatory deadlines | Submission timestamp and acknowledgement timestamp vs deadline | Regime SLA table (see section 5) |
| Regulatory acceptance | Resolve technical rejections | Accepted vs rejected and aging of unresolved rejects | No unresolved critical rejects beyond agreed SLA |
| Aggregation consistency | Keep totals coherent across chain | Count and monetary totals across expected/submitted/actual | Control totals must align within approved tolerance |
| Lifecycle/state consistency | Keep event/state evolution coherent | New/modify/terminate sequence and position-state evolution | No invalid lifecycle transitions |

## 4) Definition of "reconciled"

A population is considered reconciled when all of the following are true:

1. Completeness variance is within threshold.
2. Field-level discrepancies are within approved tolerance policy.
3. Submission and acknowledgement timing meets SLA.
4. No unresolved critical vendor/TR/ARM rejection remains open beyond SLA.
5. Aggregated totals reconcile within approved variance.
6. Lifecycle and position states are consistent for applicable regimes.
7. Corrections/resubmissions are traceable and auditable.

## 5) SLA assumptions by regime (requirements baseline)

| Regime | Timeliness assumption | Notes |
|---|---|---|
| MiFID II (EU/UK) | T+1 | ARM-based via TRAX |
| EMIR (EU/UK) | T+1 | TR-based |
| ASIC | T+2 | TR-based |
| SFTR | T+1 | Direct DTCC |
| CAT | T+1 | Event-level submission cycle |
| LTR | T+1 operational window | Based on EOD + transfer operational runbooks |
| APA | Near real-time | Event publication model |

## 6) Tolerance principles (to be refined in Step 2/3)

| Metric | Proposed baseline principle | Status |
|---|---|---|
| Population completeness | <= 1% variance | Baseline agreed |
| Notional variance | Instrument/regime-specific threshold | Pending detailed calibration |
| Price variance | Product-specific tick/percentage tolerance | Pending detailed calibration |
| Lifecycle timing drift | Event-sequence and date-window controls | Pending model-level rule design |
| Daily control totals | Expected vs submitted vs actual totals | Baseline agreed |

## 7) Explicit non-goals for this phase

- Detailed rule logic implementation
- Technical data model implementation
- Exception workflow tooling implementation
- Final threshold calibration by instrument class

## 8) Acceptance criteria checklist

- [x] Success metrics documented
- [x] Tolerance principles documented at baseline level
- [x] SLA assumptions documented
- [x] Definition of "reconciled" formalized for cross-team alignment
