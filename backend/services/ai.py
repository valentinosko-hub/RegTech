"""Mock implementations of the 5 AI calls described in ARCHITECTURE.md.

Every function below keeps the exact signature, timeout, and fallback
behaviour that Phase 4 will need. Swapping to real AI means replacing the
body of each function with an `ai_query` SQL call or a direct HTTP call to
a pay-per-token Foundation Model endpoint — callers (routers, mock_store)
never change.
"""

from __future__ import annotations

import asyncio
import re

from backend.models.cases import CaseExtraction, ExtractedStringField
from backend.models.common import JURISDICTIONS, VENDORS
from backend.models.reconciliation import BreakCategory, MappingRule, ReconBreak

EXTRACT_TIMEOUT_SECONDS = 10
EXPLAIN_TIMEOUT_SECONDS = 5
ASSESS_TIMEOUT_SECONDS = 5
BRIEFING_TIMEOUT_SECONDS = 15

_SEVERITY_KEYWORDS = {
    "P1": ["p1", "critical", "urgent", "sev1", "sla breach", "down"],
    "P2": ["p2", "high priority", "sev2", "escalate"],
    "P3": ["p3", "medium", "sev3"],
    "P4": ["p4", "low priority", "minor", "sev4"],
}
_CASE_TYPE_KEYWORDS = {
    "query": ["question", "query", "asking", "clarify", "please confirm"],
    "task": ["follow up", "follow-up", "task", "reminder", "track", "review"],
}


async def extract_case_entities(text: str) -> CaseExtraction:
    """Call 1: Case Entity Extraction (databricks-claude-sonnet-4-5, mocked).

    Fallback on timeout/failure: status="failed" -> frontend shows the
    manual entry form.
    """
    try:
        return await asyncio.wait_for(_extract(text), timeout=EXTRACT_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        return _failed_extraction()


async def _extract(raw_text: str) -> CaseExtraction:
    await asyncio.sleep(0.35)  # simulate model latency
    text = raw_text.strip()[:4000]
    if not text:
        return _failed_extraction()

    lowered = text.lower()

    jurisdiction = next((j for j in JURISDICTIONS if j.lower() in lowered), None)
    vendor = next((v for v in VENDORS if v.lower() in lowered), None)

    severity = None
    for level, keywords in _SEVERITY_KEYWORDS.items():
        if any(kw in lowered for kw in keywords):
            severity = level
            break

    case_type = "incident"
    for ctype, keywords in _CASE_TYPE_KEYWORDS.items():
        if any(kw in lowered for kw in keywords):
            case_type = ctype
            break

    first_line = next((line.strip() for line in text.splitlines() if line.strip()), text[:80])
    title = first_line[:120]

    return CaseExtraction(
        status="ok",
        title=ExtractedStringField(value=title, confidence="confident" if len(title) > 8 else "suggested"),
        severity=ExtractedStringField(value=severity, confidence="confident" if severity else "unknown"),
        jurisdiction=ExtractedStringField(
            value=jurisdiction, confidence="confident" if jurisdiction else "unknown"
        ),
        vendor=ExtractedStringField(value=vendor, confidence="confident" if vendor else "unknown"),
        case_type=ExtractedStringField(value=case_type, confidence="suggested"),
        description=ExtractedStringField(value=text, confidence="confident" if len(text) > 40 else "suggested"),
        duplicate_warning=None,
    )


def _failed_extraction() -> CaseExtraction:
    empty = ExtractedStringField(value=None, confidence="unknown")
    return CaseExtraction(
        status="failed",
        title=empty,
        severity=empty,
        jurisdiction=empty,
        vendor=empty,
        case_type=empty,
        description=empty,
        duplicate_warning=None,
    )


_CATEGORY_LABELS: dict[BreakCategory, str] = {
    "known_mapping": "a known mapping quirk",
    "value_mismatch": "a genuine value mismatch",
    "date_discrepancy": "a date formatting discrepancy",
    "missing_record": "a missing record",
    "extra_record": "an unexpected extra record",
    "novel": "a novel, previously unseen pattern",
}


async def classify_break(brk: ReconBreak) -> BreakCategory:
    """Call 2: Break Categorisation (ai_classify via SQL, mocked here as a
    small heuristic). Fallback on failure: 'novel'.
    """
    try:
        return await asyncio.wait_for(_classify(brk), timeout=5)
    except asyncio.TimeoutError:
        return "novel"


async def _classify(brk: ReconBreak) -> BreakCategory:
    await asyncio.sleep(0.5)
    source, target = brk.source_value.strip().lower(), brk.target_value.strip().lower()
    if target in ("missing", "", "—"):
        return "missing_record"
    if source == target:
        return "known_mapping"
    if re.sub(r"[^a-z0-9]", "", source) == re.sub(r"[^a-z0-9]", "", target):
        return "known_mapping"
    if "date" in brk.field_name.lower():
        return "date_discrepancy"
    return "value_mismatch" if brk.historical_frequency > 0 else "novel"


async def explain_break(brk: ReconBreak, mapping_rule: MappingRule | None) -> str:
    """Call 3: Break Explanation (on-demand, cached on the break record after
    first generation). Fallback: templated one-liner using category + count.
    """
    try:
        return await asyncio.wait_for(_explain(brk, mapping_rule), timeout=EXPLAIN_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        category_label = brk.category or "novel"
        return f"This is a {category_label} break on field '{brk.field_name}'. It has been seen {brk.historical_frequency} times previously."


async def _explain(brk: ReconBreak, mapping_rule: MappingRule | None) -> str:
    await asyncio.sleep(0.6)
    category = brk.category or "novel"
    label = _CATEGORY_LABELS.get(category, "an unclassified pattern")
    frequency_clause = (
        f"a recurring pattern seen {brk.historical_frequency} times before"
        if brk.historical_frequency > 0
        else "the first time this exact pattern has been seen"
    )
    sentence_one = (
        f"The '{brk.field_name}' field differs between source ({brk.source_value}) and target "
        f"({brk.target_value}) — this looks like {label}, {frequency_clause}."
    )
    if mapping_rule:
        sentence_two = (
            f"A mapping rule already covers this exact discrepancy ({mapping_rule.resolution_description}), "
            "so it is safe to apply the rule rather than treat it as a new issue."
        )
    elif category == "missing_record":
        sentence_two = "No matching record was found in the target system at all, so this needs vendor confirmation rather than a field-level fix."
    else:
        sentence_two = "No existing mapping rule covers this case yet, so it likely needs manual review before deciding on a resolution."
    return f"{sentence_one} {sentence_two}"


async def assess_alert(description: str, history_summary: str) -> str | None:
    """Call 4: Alert Assessment. Fallback: None (UI shows alert without AI
    context)."""
    try:
        return await asyncio.wait_for(_assess(description, history_summary), timeout=ASSESS_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        return None


async def _assess(description: str, history_summary: str) -> str:
    await asyncio.sleep(0.3)
    return (
        f"Based on recent history ({history_summary}), this appears consistent with prior occurrences — "
        "monitor for now and escalate only if it exceeds the usual recovery window."
    )


async def generate_daily_briefing(structured_summary: str) -> str:
    """Call 5: Daily Briefing. Fallback: static failure message."""
    try:
        return await asyncio.wait_for(_briefing(structured_summary), timeout=BRIEFING_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        from backend.services.mock_data import FALLBACK_BRIEFING

        return FALLBACK_BRIEFING


async def _briefing(structured_summary: str) -> str:
    await asyncio.sleep(0.4)
    return structured_summary
