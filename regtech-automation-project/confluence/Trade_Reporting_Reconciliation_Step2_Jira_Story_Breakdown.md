# Step 2 - Jira Story Breakdown (Field Mapping and Reconciliation Design)

Last updated: 2026-03-18  
Parent workstream: REG-3279 Step 2 (Data source inventory + field mapping matrix)

## 1) Why this split is needed

Manager feedback is valid: a source catalog and a reconciliation mapping matrix are not the same artifact.

- **Catalog** answers: "What sources exist, who owns them, where are they?"
- **Field mapping matrix** answers: "How does each reportable field reconcile from source to reporting to response?"

Step 2 should therefore be delivered as multiple Jira stories, not one broad ticket.

## 2) Recommended Step 2 story set

### Story A - Lock source catalog baseline (already mostly done)

**Summary**  
Finalize and sign off the source inventory baseline used for mapping.

**Scope**
- validate source owners by squad,
- validate format/frequency/storage details,
- mark ingestion status by model/endpoint.

**Acceptance criteria**
- source inventory status is Approved,
- all rows have owner + frequency + storage + migration status,
- open unknowns are tagged and assigned.

**Primary artifact**
- `Trade_Reporting_Reconciliation_Data_Source_Inventory_Catalog.md`

---

### Story B - Build field mapping matrix (core manager ask)

**Summary**  
Create field-level mapping from internal source -> reporting table -> submitted payload -> response evidence.

**Scope**
- prioritize high-risk/high-volume fields first (UTI, LEI, Notional, Price, Currency, Product, lifecycle state, event timestamps),
- include transformation rules and expected comparison method,
- include tolerance class and control owner.

**Acceptance criteria**
- at least one complete matrix per regulation family (MiFID, EMIR, ASIC),
- each mapped row includes source field and target/reporting field,
- transformation rule and validation logic are documented.

**Primary artifact**
- `Trade_Reporting_Reconciliation_Field_Mapping_Matrix.md`

---

### Story C - Response and rejection mapping

**Summary**  
Map response files/status codes to reportable fields and reconciliation outcomes.

**Scope**
- TR/ARM/CAT/APA response schema mapping,
- accepted/rejected/corrected status interpretation,
- unresolved rejection aging logic.

**Acceptance criteria**
- status code mapping table documented per endpoint,
- each status class linked to control severity and action owner,
- unresolved reject workflow assumptions captured.

---

### Story D - Rule specification and tolerance policy

**Summary**  
Convert mapped fields into explicit reconciliation rule definitions.

**Scope**
- exact-match vs tolerance-match categories,
- numeric tolerances by field class,
- null/default behavior and lifecycle sequencing rules.

**Acceptance criteria**
- rules documented for core fields per model,
- tolerance policy approved by Ops/Compliance stakeholders,
- exception categories standardized (Critical/Warning/Advisory).

---

### Story E - Pilot runbook and evidence pack

**Summary**  
Run one pilot cycle for selected model(s) and produce auditable evidence.

**Scope**
- run matrix-driven checks for one cycle,
- capture mismatches and root causes,
- refine mappings/rules from pilot findings.

**Acceptance criteria**
- pilot evidence pack produced,
- mismatch root-cause categories documented,
- backlog updates created for unresolved data/ingestion gaps.

## 3) Suggested implementation order

1. Story A (catalog sign-off)  
2. Story B (field matrix core)  
3. Story C (response/rejection semantics)  
4. Story D (rules/tolerances)  
5. Story E (pilot evidence)

## 4) Suggested Jira wording for manager alignment

Use this short message in Jira updates:

> We completed the **source inventory baseline** (catalog artifact).  
> The next deliverable is the **field-level reconciliation mapping matrix** (source -> reporting -> response by field), which is a separate artifact and is now split into dedicated Step 2 stories.
