"""Deterministic-but-lively generators for RegOps Hub's Phase 1 mock dataset.

Every function here returns the same Pydantic models that the API contracts
use, so Phase 2/3 can replace the *contents* of these functions with real
asyncpg / databricks-sql-connector queries without touching routers,
services callers, or the frontend.

Data is generated once at process start, anchored to "now" so it always
looks like "today's operations" whenever the app is opened, and mutated
in-place afterwards by user actions (resolving a break, closing a case...).
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from backend.models.cases import Case, Comment, LinkedItem, TimelineEvent
from backend.models.common import JURISDICTIONS, VENDORS
from backend.models.monitoring import Alert, AlertHistoryPoint, FeedStatusItem, ReportSubmission
from backend.models.notifications import Notification
from backend.models.reconciliation import MappingRule, ReconBreak, ReconRun


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _day_key(now: datetime) -> str:
    return now.strftime("%Y-%m-%d")


def _due(now: datetime, hour: int, minute: int = 0) -> datetime:
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)


# ---------------------------------------------------------------------------
# Regulatory reports
# ---------------------------------------------------------------------------

REPORT_CATALOG = [
    ("MiFID II Transaction Report (RTS 22)", "MiFID", 7, 0, "UnaVista"),
    ("FCA Transaction Report", "FCA", 8, 0, "Cappitech"),
    ("ASIC Derivative Transaction Report", "ASIC", 9, 0, "DTCC"),
    ("MAS Position Report", "MAS", 12, 0, "Kaizen"),
    ("MAS Large Exposure Report", "MAS", 14, 0, "Cappitech"),
    ("ASIC Rewrite Regulatory Report", "ASIC", 15, 0, "DTCC"),
    ("EMIR Valuation Report", "EMIR", 20, 0, "Kaizen"),
    ("MiFID Best Execution Report (RTS 27)", "MiFID", 17, 0, "UnaVista"),
    ("EMIR Trade Report", "EMIR", 23, 0, "DTCC"),
]

FAILURE_REASONS = [
    "Validation failed: 14 records missing counterparty LEI on field counterpartyLEI",
    "Vendor gateway timeout after 3 retries (SFTP handshake)",
    "Schema mismatch: unexpected field 'settlementCcy' in batch 00231",
    "Reconciliation pre-check failed: source extract 6% below expected volume",
    "Upstream trade capture system returned partial file (checksum mismatch)",
]


def generate_report_submissions(now: datetime) -> list[ReportSubmission]:
    day = _day_key(now)
    out: list[ReportSubmission] = []
    for idx, (name, jurisdiction, hour, minute, _vendor) in enumerate(REPORT_CATALOG):
        rng = random.Random(f"{name}|{day}")
        due = _due(now, hour, minute)
        delta_min = (due - now).total_seconds() / 60

        started_at = None
        submitted_at = None
        acknowledged_at = None
        sla_met = None
        record_count = None
        error_message = None
        sla_state = None
        estimated_completion = None

        if delta_min > 180:
            status = "scheduled"
        elif delta_min > 45:
            status = rng.choice(["generating", "validating"])
            started_at = due - timedelta(minutes=rng.randint(60, 150))
            sla_state = "at_risk" if rng.random() < 0.15 else "on_track"
            estimated_completion = due - timedelta(minutes=rng.randint(5, 30))
        elif delta_min > 0:
            status = "queued"
            started_at = due - timedelta(minutes=rng.randint(80, 170))
            sla_state = "at_risk" if delta_min < 20 or rng.random() < 0.25 else "on_track"
            estimated_completion = now + timedelta(minutes=max(4, int(delta_min * 0.6)))
        else:
            outcome = rng.random()
            started_at = due - timedelta(minutes=rng.randint(90, 180))
            if outcome < 0.72:
                status = "acknowledged" if rng.random() < 0.6 else "submitted"
                submitted_at = due - timedelta(minutes=rng.randint(2, 25))
                if status == "acknowledged":
                    acknowledged_at = submitted_at + timedelta(minutes=rng.randint(1, 15))
                sla_met = True
                sla_state = "met"
                record_count = rng.randint(1_200, 48_000)
            elif outcome < 0.90:
                status = "submitted"
                submitted_at = due + timedelta(minutes=rng.randint(1, 20))
                sla_met = False
                sla_state = "breached"
                record_count = rng.randint(1_200, 48_000)
            else:
                status = "failed"
                sla_met = False
                sla_state = "breached"
                error_message = rng.choice(FAILURE_REASONS)

        out.append(
            ReportSubmission(
                submission_id=f"SUB-{day.replace('-', '')}-{idx + 1:03d}",
                report_name=name,
                jurisdiction=jurisdiction,
                reporting_period=day,
                status=status,
                due_time=due,
                started_at=started_at,
                submitted_at=submitted_at,
                acknowledged_at=acknowledged_at,
                sla_met=sla_met,
                record_count=record_count,
                error_message=error_message,
                sla_state=sla_state,
                estimated_completion=estimated_completion,
            )
        )
    out.sort(key=lambda s: s.due_time)
    return out


# ---------------------------------------------------------------------------
# Feed status
# ---------------------------------------------------------------------------

FEED_CADENCE = {"Cappitech": 15, "Kaizen": 30, "UnaVista": 15, "DTCC": 60}
# Cappitech runs a persistent minor delay in the mock dataset — it feeds the
# recurring "Cappitech feed delayed" alert and case narrative used elsewhere.
FEED_HEALTH_OVERRIDE = {"Cappitech": "delayed"}


def generate_feed_status(now: datetime) -> list[FeedStatusItem]:
    day = _day_key(now)
    items: list[FeedStatusItem] = []
    for vendor in VENDORS:
        cadence = FEED_CADENCE[vendor]
        rng = random.Random(f"{vendor}-feed|{day}")
        status = FEED_HEALTH_OVERRIDE.get(vendor)
        if status is None:
            roll = rng.random()
            status = "healthy" if roll < 0.88 else "delayed"

        if status == "healthy":
            delay = 0
            last_received = now - timedelta(minutes=rng.randint(1, max(1, cadence - 1)))
        elif status == "delayed":
            delay = rng.randint(cadence + 3, cadence + 25)
            last_received = now - timedelta(minutes=cadence + delay)
        else:
            delay = rng.randint(cadence * 4, cadence * 8)
            last_received = now - timedelta(minutes=delay)

        items.append(
            FeedStatusItem(
                vendor=vendor,
                status=status,
                last_received_at=last_received,
                expected_cadence_minutes=cadence,
                delay_minutes=delay,
            )
        )
    order = {"failed": 0, "delayed": 1, "healthy": 2}
    items.sort(key=lambda f: order[f.status])
    return items


# ---------------------------------------------------------------------------
# Alerts (monitoring_events)
# ---------------------------------------------------------------------------

_ALERT_SEED = [
    dict(
        event_id="EVT-8841",
        event_type="feed_delay",
        source_vendor="Cappitech",
        source_report="FCA Transaction Report",
        severity="warning",
        description=(
            "Cappitech feed delayed 21 minutes against a 15-minute expected cadence. "
            "FCA Transaction Report generation has not started."
        ),
        status="active",
        detected_offset_min=-38,
        late_count=6,
        avg_recovery=27,
        recommended_action="Monitor for 15 more minutes; escalate to Cappitech ops if delay exceeds 40 minutes.",
    ),
    dict(
        event_id="EVT-8839",
        event_type="sla_warning",
        source_vendor="Cappitech",
        source_report="MAS Large Exposure Report",
        severity="warning",
        description=(
            "MAS Large Exposure Report is tracking 12 minutes behind its usual generation pace; "
            "estimated completion is within SLA but margin is thin."
        ),
        status="active",
        detected_offset_min=-52,
        late_count=2,
        avg_recovery=9,
        recommended_action="No action needed yet — recheck at next polling interval before deadline.",
    ),
    dict(
        event_id="EVT-8836",
        event_type="volume_anomaly",
        source_vendor="DTCC",
        source_report="EMIR Trade Report",
        severity="critical",
        description=(
            "EMIR Trade Report record count is 40% below the 30-day trailing average "
            "(12,480 vs. average 20,750). Possible upstream capture gap."
        ),
        status="active",
        detected_offset_min=-95,
        late_count=1,
        avg_recovery=64,
        recommended_action="Escalate to trade capture team; confirm whether a source feed dropped a batch before resubmitting.",
    ),
    dict(
        event_id="EVT-8801",
        event_type="sla_breach",
        source_vendor="DTCC",
        source_report="ASIC Rewrite Regulatory Report",
        severity="critical",
        description=(
            "ASIC Rewrite Regulatory Report missed its 15:00 deadline by 34 minutes due to a "
            "DTCC gateway timeout."
        ),
        status="resolved",
        detected_offset_min=-26 * 60,
        late_count=4,
        avg_recovery=31,
        recommended_action="Resolved — resubmitted successfully. No further action.",
    ),
    dict(
        event_id="EVT-8794",
        event_type="feed_failure",
        source_vendor="Kaizen",
        source_report="EMIR Valuation Report",
        severity="critical",
        description="Kaizen feed connection dropped mid-transfer; valuation batch had to be re-pulled.",
        status="resolved",
        detected_offset_min=-30 * 60,
        late_count=3,
        avg_recovery=22,
        recommended_action="Resolved — feed reconnected automatically after 18 minutes.",
    ),
]

_ASSESSMENTS = {
    "EVT-8841": "This matches Cappitech's known mid-morning delay pattern; expect recovery within 20-30 minutes, monitor rather than escalate.",
    "EVT-8839": "Slight pacing slip on a low-volume report — historically resolves itself well inside SLA, safe to monitor.",
    "EVT-8836": "A volume drop this large is not typical for EMIR Trade Report and warrants escalation to confirm no upstream batch was dropped.",
    "EVT-8801": "This was a one-off vendor timeout consistent with DTCC's occasional gateway hiccups; already resolved via resubmission.",
    "EVT-8794": "Transient connection drop, recovered automatically; no recurring pattern detected in the last 30 days.",
}


def generate_alerts(now: datetime) -> list[Alert]:
    out = []
    for seed in _ALERT_SEED:
        detected_at = now + timedelta(minutes=seed["detected_offset_min"])
        out.append(
            Alert(
                event_id=seed["event_id"],
                event_type=seed["event_type"],
                source_vendor=seed["source_vendor"],
                source_report=seed["source_report"],
                severity=seed["severity"],
                description=seed["description"],
                ai_assessment=_ASSESSMENTS[seed["event_id"]],
                status=seed["status"],
                detected_at=detected_at,
                resolved_at=(detected_at + timedelta(minutes=seed["avg_recovery"]))
                if seed["status"] != "active"
                else None,
            )
        )
    out.sort(key=lambda a: (a.status != "active", a.severity != "critical", a.detected_at), reverse=False)
    return out


def alert_history(now: datetime, seed: dict) -> list[AlertHistoryPoint]:
    rng = random.Random(f"history|{seed['event_id']}")
    points = []
    for i in range(10, 0, -1):
        date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        points.append(
            AlertHistoryPoint(
                date=date,
                late_by_minutes=rng.randint(0, seed["late_count"] and 45 or 5),
                recovery_minutes=rng.randint(5, max(6, seed["avg_recovery"] + 15)),
            )
        )
    return points


ALERT_SEED_BY_ID = {seed["event_id"]: seed for seed in _ALERT_SEED}


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------


def _pct(a: int, b: int) -> float:
    return round(100 * a / b, 2) if b else 100.0


def generate_recon_data(
    now: datetime,
) -> tuple[list[ReconRun], list[ReconBreak], list[MappingRule], dict[str, MappingRule]]:
    day = _day_key(now)
    mapping_rules = [
        MappingRule(
            id="MAP-001",
            field_pattern="tradeDate",
            source_pattern="YYYY-MM-DD",
            target_pattern="DD/MM/YYYY",
            resolution_description="UnaVista returns trade date in DD/MM/YYYY; OMS emits ISO 8601. Known format-only mismatch, safe to normalize and match.",
        ),
        MappingRule(
            id="MAP-002",
            field_pattern="venueMIC",
            source_pattern="4-char MIC",
            target_pattern="4-char MIC + trailing space",
            resolution_description="Kaizen occasionally pads venue MIC codes with a trailing space in fixed-width extracts.",
        ),
        MappingRule(
            id="MAP-003",
            field_pattern="counterpartyLEI",
            source_pattern="uppercase alphanumeric",
            target_pattern="lowercase alphanumeric",
            resolution_description="DTCC swap data repository lowercases LEI codes in its export; OMS keeps issued casing.",
        ),
        MappingRule(
            id="MAP-004",
            field_pattern="notionalCurrency",
            source_pattern="settlement currency",
            target_pattern="quote currency",
            resolution_description="Cappitech reports notional in quote currency for cross-currency instruments while OMS books in settlement currency; both values are correct, just different conventions.",
        ),
    ]
    mapping_by_id = {m.id: m for m in mapping_rules}

    runs_seed = [
        dict(
            run_id=f"RUN-{day.replace('-', '')}-ASIC",
            recon_set_name="ASIC Derivative Transaction Recon",
            jurisdiction="ASIC",
            source_count=18_420,
            target_count=18_416,
        ),
        dict(
            run_id=f"RUN-{day.replace('-', '')}-MIFID",
            recon_set_name="MiFID Transaction Recon",
            jurisdiction="MiFID",
            source_count=52_108,
            target_count=52_105,
        ),
        dict(
            run_id=f"RUN-{day.replace('-', '')}-EMIR",
            recon_set_name="EMIR Trade Recon",
            jurisdiction="EMIR",
            source_count=20_750,
            target_count=20_744,
        ),
        dict(
            run_id=f"RUN-{day.replace('-', '')}-FCA",
            recon_set_name="FCA Transaction Recon",
            jurisdiction="FCA",
            source_count=41_290,
            target_count=41_290,
        ),
        dict(
            run_id=f"RUN-{day.replace('-', '')}-MAS",
            recon_set_name="MAS Position Recon",
            jurisdiction="MAS",
            source_count=9_812,
            target_count=9_810,
        ),
    ]

    breaks: list[ReconBreak] = []

    def add_break(
        run_id: str,
        recon_set_name: str,
        jurisdiction: str,
        field_name: str,
        source_value: str,
        target_value: str,
        category: str | None,
        historical_frequency: int,
        source_record: dict[str, str],
        target_record: dict[str, str],
        mapping_rule_id: str | None,
        idx: int,
        created_offset_min: int,
    ) -> ReconBreak:
        b = ReconBreak(
            break_id=f"{run_id}-BRK{idx:02d}",
            run_id=run_id,
            recon_set_name=recon_set_name,
            jurisdiction=jurisdiction,
            field_name=field_name,
            source_value=source_value,
            target_value=target_value,
            source_record=source_record,
            target_record=target_record,
            category=category,
            historical_frequency=historical_frequency,
            ai_explanation=None,
            status="open",
            resolution_type=None,
            resolution_note=None,
            resolved_by=None,
            resolved_at=None,
            linked_case_id=None,
            linked_mapping_rule_id=mapping_rule_id,
            created_at=now - timedelta(minutes=created_offset_min),
        )
        breaks.append(b)
        return b

    # ASIC — 4 breaks
    run_id = runs_seed[0]["run_id"]
    add_break(
        run_id, "ASIC Derivative Transaction Recon", "ASIC",
        "counterpartyLEI", "549300GS4CH2M56SW906", "549300gs4ch2m56sw906",
        "known_mapping", 22,
        {"tradeId": "ASX-7724193", "instrument": "AUD/USD Swap", "notionalAmount": "5,000,000.00 AUD", "counterpartyLEI": "549300GS4CH2M56SW906", "tradeDate": "2026-07-20"},
        {"tradeId": "ASX-7724193", "instrument": "AUD/USD Swap", "notionalAmount": "5,000,000.00 AUD", "counterpartyLEI": "549300gs4ch2m56sw906", "tradeDate": "2026-07-20"},
        "MAP-003", 1, 210,
    )
    add_break(
        run_id, "ASIC Derivative Transaction Recon", "ASIC",
        "notionalAmount", "2,150,000.00 AUD", "2,150,000.00 USD",
        "value_mismatch", 3,
        {"tradeId": "ASX-7724201", "instrument": "AUD IRS 5Y", "notionalAmount": "2,150,000.00 AUD", "counterpartyLEI": "213800WVKUQ3V5B3F783", "tradeDate": "2026-07-20"},
        {"tradeId": "ASX-7724201", "instrument": "AUD IRS 5Y", "notionalAmount": "2,150,000.00 USD", "counterpartyLEI": "213800WVKUQ3V5B3F783", "tradeDate": "2026-07-20"},
        None, 2, 195,
    )
    add_break(
        run_id, "ASIC Derivative Transaction Recon", "ASIC",
        "settlementDate", "2026-07-22", "22/07/2026",
        "date_discrepancy", 41,
        {"tradeId": "ASX-7724233", "instrument": "FX Forward", "notionalAmount": "800,000.00 AUD", "counterpartyLEI": "5493006KMZ5T7SS8SD30", "settlementDate": "2026-07-22"},
        {"tradeId": "ASX-7724233", "instrument": "FX Forward", "notionalAmount": "800,000.00 AUD", "counterpartyLEI": "5493006KMZ5T7SS8SD30", "settlementDate": "22/07/2026"},
        "MAP-001", 3, 180,
    )
    add_break(
        run_id, "ASIC Derivative Transaction Recon", "ASIC",
        "record", "present", "missing",
        "missing_record", 0,
        {"tradeId": "ASX-7724280", "instrument": "AUD IRS 2Y", "notionalAmount": "1,000,000.00 AUD", "counterpartyLEI": "549300QXKY42V6EMCT96", "tradeDate": "2026-07-20"},
        {"tradeId": "—", "instrument": "—", "notionalAmount": "—", "counterpartyLEI": "—", "tradeDate": "—"},
        None, 4, 165,
    )
    add_break(
        run_id, "ASIC Derivative Transaction Recon", "ASIC",
        "tradeDate", "2026-07-21", "21-07-2026",
        None, 0,
        {"tradeId": "ASX-7724302", "instrument": "AUD IRS 4Y", "notionalAmount": "1,650,000.00 AUD", "counterpartyLEI": "213800H4O108K5S7NV21", "tradeDate": "2026-07-21"},
        {"tradeId": "ASX-7724302", "instrument": "AUD IRS 4Y", "notionalAmount": "1,650,000.00 AUD", "counterpartyLEI": "213800H4O108K5S7NV21", "tradeDate": "21-07-2026"},
        None, 5, 3,
    )

    # MiFID — 3 breaks
    run_id = runs_seed[1]["run_id"]
    add_break(
        run_id, "MiFID Transaction Recon", "MiFID",
        "tradeDate", "2026-07-20", "20/07/2026",
        "known_mapping", 63,
        {"tradeId": "MFD-1120044", "instrument": "AAPL Equity", "notionalAmount": "48,200.00 EUR", "counterpartyLEI": "213800MBWEIJDM5CU638", "tradeDate": "2026-07-20"},
        {"tradeId": "MFD-1120044", "instrument": "AAPL Equity", "notionalAmount": "48,200.00 EUR", "counterpartyLEI": "213800MBWEIJDM5CU638", "tradeDate": "20/07/2026"},
        "MAP-001", 1, 140,
    )
    add_break(
        run_id, "MiFID Transaction Recon", "MiFID",
        "venueMIC", "XLON", "XLON ",
        "novel", 0,
        {"tradeId": "MFD-1120077", "instrument": "VOD.L Equity", "notionalAmount": "12,900.00 GBP", "counterpartyLEI": "213800WSGIIZCXF1P572", "venueMIC": "XLON"},
        {"tradeId": "MFD-1120077", "instrument": "VOD.L Equity", "notionalAmount": "12,900.00 GBP", "counterpartyLEI": "213800WSGIIZCXF1P572", "venueMIC": "XLON "},
        None, 2, 120,
    )
    add_break(
        run_id, "MiFID Transaction Recon", "MiFID",
        "notionalAmount", "9,450.00 EUR", "9,540.00 EUR",
        "value_mismatch", 5,
        {"tradeId": "MFD-1120091", "instrument": "SAP Equity", "notionalAmount": "9,450.00 EUR", "counterpartyLEI": "529900S21GBH3RPGCX85", "tradeDate": "2026-07-20"},
        {"tradeId": "MFD-1120091", "instrument": "SAP Equity", "notionalAmount": "9,540.00 EUR", "counterpartyLEI": "529900S21GBH3RPGCX85", "tradeDate": "2026-07-20"},
        None, 3, 95,
    )

    # EMIR — 5 breaks (largest, ties into the volume-anomaly alert)
    run_id = runs_seed[2]["run_id"]
    add_break(
        run_id, "EMIR Trade Recon", "EMIR",
        "venueMIC", "XETR", "XETR ",
        "known_mapping", 34,
        {"tradeId": "EMR-88231", "instrument": "EUR/GBP FX Swap", "notionalAmount": "3,200,000.00 EUR", "counterpartyLEI": "391200QXGLWHK9VK6M27", "venueMIC": "XETR"},
        {"tradeId": "EMR-88231", "instrument": "EUR/GBP FX Swap", "notionalAmount": "3,200,000.00 EUR", "counterpartyLEI": "391200QXGLWHK9VK6M27", "venueMIC": "XETR "},
        "MAP-002", 1, 260,
    )
    add_break(
        run_id, "EMIR Trade Recon", "EMIR",
        "notionalCurrency", "EUR", "USD",
        "known_mapping", 17,
        {"tradeId": "EMR-88254", "instrument": "EUR/USD Cross-Currency Swap", "notionalAmount": "4,800,000.00", "notionalCurrency": "EUR", "counterpartyLEI": "969500SVEZ9V9BFDW431"},
        {"tradeId": "EMR-88254", "instrument": "EUR/USD Cross-Currency Swap", "notionalAmount": "4,800,000.00", "notionalCurrency": "USD", "counterpartyLEI": "969500SVEZ9V9BFDW431"},
        "MAP-004", 2, 240,
    )
    add_break(
        run_id, "EMIR Trade Recon", "EMIR",
        "record", "present", "missing",
        "missing_record", 0,
        {"tradeId": "EMR-88301", "instrument": "EUR IRS 10Y", "notionalAmount": "6,500,000.00 EUR", "counterpartyLEI": "5299009Y4EWA5B8QVU48", "tradeDate": "2026-07-20"},
        {"tradeId": "—", "instrument": "—", "notionalAmount": "—", "counterpartyLEI": "—", "tradeDate": "—"},
        None, 3, 220,
    )
    add_break(
        run_id, "EMIR Trade Recon", "EMIR",
        "record", "present", "missing",
        "missing_record", 0,
        {"tradeId": "EMR-88312", "instrument": "EUR IRS 7Y", "notionalAmount": "3,900,000.00 EUR", "counterpartyLEI": "213800K1F9CH8IGB1H83", "tradeDate": "2026-07-20"},
        {"tradeId": "—", "instrument": "—", "notionalAmount": "—", "counterpartyLEI": "—", "tradeDate": "—"},
        None, 4, 200,
    )
    add_break(
        run_id, "EMIR Trade Recon", "EMIR",
        "settlementDate", "2026-07-24", "24/07/2026",
        "date_discrepancy", 41,
        {"tradeId": "EMR-88340", "instrument": "EUR FX Forward", "notionalAmount": "1,100,000.00 EUR", "counterpartyLEI": "529900W18LQJJN6SJ336", "settlementDate": "2026-07-24"},
        {"tradeId": "EMR-88340", "instrument": "EUR FX Forward", "notionalAmount": "1,100,000.00 EUR", "counterpartyLEI": "529900W18LQJJN6SJ336", "settlementDate": "24/07/2026"},
        "MAP-001", 5, 180,
    )

    # MAS — 2 breaks
    run_id = runs_seed[4]["run_id"]
    add_break(
        run_id, "MAS Position Recon", "MAS",
        "notionalAmount", "780,000.00 SGD", "781,500.00 SGD",
        "value_mismatch", 2,
        {"tradeId": "MAS-55021", "instrument": "SGD IRS 3Y", "notionalAmount": "780,000.00 SGD", "counterpartyLEI": "549300FGJPPK4XG5RM31", "tradeDate": "2026-07-20"},
        {"tradeId": "MAS-55021", "instrument": "SGD IRS 3Y", "notionalAmount": "781,500.00 SGD", "counterpartyLEI": "549300FGJPPK4XG5RM31", "tradeDate": "2026-07-20"},
        None, 1, 100,
    )
    add_break(
        run_id, "MAS Position Recon", "MAS",
        "counterpartyLEI", "254900NMDPXOKZ2NCV27", "254900nmdpxokz2ncv27",
        "known_mapping", 22,
        {"tradeId": "MAS-55048", "instrument": "USD/SGD FX Swap", "notionalAmount": "2,400,000.00 SGD", "counterpartyLEI": "254900NMDPXOKZ2NCV27", "tradeDate": "2026-07-20"},
        {"tradeId": "MAS-55048", "instrument": "USD/SGD FX Swap", "notionalAmount": "2,400,000.00 SGD", "counterpartyLEI": "254900nmdpxokz2ncv27", "tradeDate": "2026-07-20"},
        "MAP-003", 2, 80,
    )

    breaks_by_run: dict[str, list[ReconBreak]] = {}
    for b in breaks:
        breaks_by_run.setdefault(b.run_id, []).append(b)

    runs: list[ReconRun] = []
    for seed in runs_seed:
        run_breaks = breaks_by_run.get(seed["run_id"], [])
        break_count = len(run_breaks)
        open_count = sum(1 for b in run_breaks if b.status == "open")
        matched = seed["target_count"] - break_count
        runs.append(
            ReconRun(
                run_id=seed["run_id"],
                recon_set_name=seed["recon_set_name"],
                jurisdiction=seed["jurisdiction"],
                run_date=day,
                source_count=seed["source_count"],
                target_count=seed["target_count"],
                matched_count=matched,
                break_count=break_count,
                open_break_count=open_count,
                match_rate=_pct(matched, seed["target_count"]),
                status="completed",
                reviewed_by=None,
                signed_off_at=None,
            )
        )
    runs.sort(key=lambda r: (r.open_break_count == 0, -r.open_break_count))
    return runs, breaks, mapping_rules, mapping_by_id


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------

_CASE_SEED = [
    dict(
        title="Cappitech FCA feed recurring 15-20min delay — pattern investigation",
        severity="P3",
        status="investigating",
        jurisdiction="FCA",
        vendor="Cappitech",
        case_type="task",
        owner="Jess Harrow",
        source_type="monitoring_alert",
        source_ref="EVT-8841",
        age_hours=30,
        description="Cappitech's FCA feed has missed its 15-minute cadence six times in the last 30 days. Opening a task to review with vendor whether SLA needs renegotiating or our polling window needs adjusting.",
    ),
    dict(
        title="EMIR Trade Report volume anomaly — 40% below trailing average",
        severity="P1",
        status="open",
        jurisdiction="EMIR",
        vendor="DTCC",
        case_type="incident",
        owner="Jess Harrow",
        source_type="monitoring_alert",
        source_ref="EVT-8836",
        age_hours=1,
        description="Today's EMIR Trade Report extract returned 12,480 records vs. a 30-day trailing average of 20,750 (-40%). Investigating whether the upstream trade capture batch dropped a segment before resubmission.",
    ),
    dict(
        title="ASIC recon: missing record ASX-7724280 not present in DTCC swap repository",
        severity="P2",
        status="open",
        jurisdiction="ASIC",
        vendor="DTCC",
        case_type="incident",
        owner="Marcus Odei",
        source_type="recon_break",
        source_ref=None,  # linked after break generation
        age_hours=4,
        description="Trade ASX-7724280 (AUD IRS 2Y, notional 1,000,000.00 AUD) is present in the OMS extract but absent from DTCC's swap data repository target file. Escalating for vendor confirmation of receipt.",
    ),
    dict(
        title="Vendor query: Kaizen valuation batch reconnection window",
        severity="P4",
        status="pending_vendor",
        jurisdiction="EMIR",
        vendor="Kaizen",
        case_type="query",
        owner="Priya Nandan",
        source_type="manual",
        source_ref=None,
        age_hours=52,
        description="Following the feed drop on EVT-8794, asked Kaizen support to confirm root cause and whether a permanent fix is planned. Awaiting their written response.",
    ),
    dict(
        title="MAS Large Exposure Report — confirm SLA margin after Cappitech pacing slip",
        severity="P3",
        status="pending_vendor",
        jurisdiction="MAS",
        vendor="Cappitech",
        case_type="task",
        owner="Priya Nandan",
        source_type="monitoring_alert",
        source_ref="EVT-8839",
        age_hours=6,
        description="Report is tracking 12 minutes behind pace; opened to track outcome and follow up with Cappitech if this becomes a repeat pattern this month.",
    ),
    dict(
        title="MiFID RTS27 best-ex report: quarterly review action items",
        severity="P4",
        status="open",
        jurisdiction="MiFID",
        vendor="UnaVista",
        case_type="task",
        owner="Marcus Odei",
        source_type="manual",
        source_ref=None,
        age_hours=96,
        description="Tracking three follow-up items from this quarter's best execution report review with compliance. Not urgent, revisit before month end.",
    ),
    dict(
        title="DTCC gateway timeout caused ASIC Rewrite Report SLA breach",
        severity="P2",
        status="closed",
        jurisdiction="ASIC",
        vendor="DTCC",
        case_type="incident",
        owner="Jess Harrow",
        source_type="monitoring_alert",
        source_ref="EVT-8801",
        age_hours=27,
        description="Report missed its 15:00 deadline by 34 minutes due to a DTCC gateway timeout. Resubmitted successfully at 15:38.",
        resolution_type="resolved_with_note",
        resolution_note="Resubmission succeeded on first retry once DTCC gateway recovered. No data integrity issues found. Logged as a vendor-side transient outage.",
    ),
    dict(
        title="EMIR valuation feed dropped mid-transfer (Kaizen)",
        severity="P3",
        status="closed",
        jurisdiction="EMIR",
        vendor="Kaizen",
        case_type="incident",
        owner="Priya Nandan",
        source_type="monitoring_alert",
        source_ref="EVT-8794",
        age_hours=31,
        description="Kaizen connection dropped mid-transfer during the valuation batch pull.",
        resolution_type="resolved_with_note",
        resolution_note="Feed reconnected automatically after 18 minutes and batch was re-pulled in full. Confirmed record counts matched expected volume.",
    ),
    dict(
        title="Quarterly LEI renewal — three counterparties expiring within 30 days",
        severity="P3",
        status="investigating",
        jurisdiction="EMIR",
        vendor=None,
        case_type="task",
        owner="Marcus Odei",
        source_type="manual",
        source_ref=None,
        age_hours=72,
        description="GLEIF renewal check flagged three counterparty LEIs expiring within 30 days. Chasing counterparties for renewal confirmation before they lapse.",
    ),
    dict(
        title="UnaVista ARM maintenance window — confirm no impact to RTS22 window",
        severity="P4",
        status="open",
        jurisdiction="MiFID",
        vendor="UnaVista",
        case_type="query",
        owner="Jess Harrow",
        source_type="manual",
        source_ref=None,
        age_hours=12,
        description="UnaVista notified a maintenance window this weekend. Confirming with them it won't overlap with Monday's RTS22 submission cutoff.",
    ),
    dict(
        title="Duplicate trade suspected in MAS position feed (MAS-55021)",
        severity="P3",
        status="open",
        jurisdiction="MAS",
        vendor="Kaizen",
        case_type="incident",
        owner="Priya Nandan",
        source_type="recon_break",
        source_ref=None,
        age_hours=3,
        description="Notional mismatch on MAS-55021 (780,000.00 vs 781,500.00 SGD) may indicate a partial fill was booked twice upstream. Checking with trade capture team.",
    ),
    dict(
        title="New analyst onboarding — RegOps Hub access & saved views walkthrough",
        severity="P4",
        status="closed",
        jurisdiction=None,
        vendor=None,
        case_type="task",
        owner="Jess Harrow",
        source_type="manual",
        source_ref=None,
        age_hours=140,
        description="Walkthrough task for new team member onboarding onto monitoring and reconciliation workflows.",
        resolution_type="resolved_with_note",
        resolution_note="Completed walkthrough and access provisioning on schedule.",
    ),
]

_COMMENT_SEED = {
    0: [
        ("Jess Harrow", "Pulled the last 30 days of feed timestamps — 6 late arrivals, avg recovery 27 minutes, all self-resolved."),
        ("Marcus Odei", "Agree it's not urgent but worth a quarterly review with Cappitech account manager."),
    ],
    1: [
        ("Jess Harrow", "Checked trade capture logs — batch 3 of 4 for APAC session appears to have failed silently around 03:10 UTC."),
    ],
    2: [
        ("Marcus Odei", "Sent trade confirmation to DTCC support with the trade blotter attached."),
    ],
    3: [
        ("Priya Nandan", "Kaizen acknowledged the ticket, said RCA is in progress, ETA end of week."),
    ],
    6: [
        ("Jess Harrow", "Root cause confirmed as DTCC-side gateway timeout, not ours. Closing with vendor incident reference DTCC-INC-55210."),
    ],
    7: [
        ("Priya Nandan", "Confirmed record counts post re-pull matched the expected volume exactly. Closing out."),
    ],
    10: [
        ("Priya Nandan", "Trade capture confirmed a partial fill was booked as two separate tickets by mistake — correcting upstream."),
    ],
}


def generate_cases(now: datetime, break_link_map: dict[int, str]) -> tuple[
    list[Case], dict[str, list[TimelineEvent]], dict[str, list[Comment]], dict[str, list[LinkedItem]]
]:
    cases: list[Case] = []
    timelines: dict[str, list[TimelineEvent]] = {}
    comments: dict[str, list[Comment]] = {}
    linked_items: dict[str, list[LinkedItem]] = {}

    for idx, seed in enumerate(_CASE_SEED):
        case_id = f"INC-{2851 + idx}"
        created_at = now - timedelta(hours=seed["age_hours"])
        updated_at = created_at
        closed_at = None
        status = seed["status"]

        source_ref = seed["source_ref"]
        if source_ref is None and idx in break_link_map:
            source_ref = break_link_map[idx]

        events = [
            TimelineEvent(
                id=f"{case_id}-EVT1",
                case_id=case_id,
                event_type="created",
                actor=seed["owner"],
                description=f"Case created from {seed['source_type'].replace('_', ' ')}.",
                metadata={"sourceRef": source_ref} if source_ref else None,
                created_at=created_at,
            )
        ]

        for c_idx, (author, body) in enumerate(_COMMENT_SEED.get(idx, [])):
            c_time = created_at + timedelta(hours=(c_idx + 1) * seed["age_hours"] / (len(_COMMENT_SEED.get(idx, [])) + 2))
            comments.setdefault(case_id, []).append(
                Comment(id=f"{case_id}-CMT{c_idx + 1}", case_id=case_id, author=author, body=body, created_at=c_time)
            )
            events.append(
                TimelineEvent(
                    id=f"{case_id}-EVT{c_idx + 2}",
                    case_id=case_id,
                    event_type="comment_added",
                    actor=author,
                    description="Added a comment.",
                    metadata=None,
                    created_at=c_time,
                )
            )
            updated_at = c_time

        resolution_type = seed.get("resolution_type")
        resolution_note = seed.get("resolution_note")
        if status == "closed":
            closed_at = created_at + timedelta(hours=max(1, seed["age_hours"] - 2))
            events.append(
                TimelineEvent(
                    id=f"{case_id}-EVTCLOSE",
                    case_id=case_id,
                    event_type="closed",
                    actor=seed["owner"],
                    description=resolution_note or "Case closed.",
                    metadata={"resolutionType": resolution_type},
                    created_at=closed_at,
                )
            )
            updated_at = closed_at
        elif status in ("investigating", "pending_vendor"):
            status_change_time = created_at + timedelta(hours=min(seed["age_hours"] - 0.5, seed["age_hours"] * 0.4))
            events.append(
                TimelineEvent(
                    id=f"{case_id}-EVTSTATUS",
                    case_id=case_id,
                    event_type="status_changed",
                    actor=seed["owner"],
                    description=f"Status changed to {status.replace('_', ' ')}.",
                    metadata={"status": status},
                    created_at=status_change_time,
                )
            )
            updated_at = max(updated_at, status_change_time)

        events.sort(key=lambda e: e.created_at)
        timelines[case_id] = events

        links: list[LinkedItem] = []
        if seed["source_type"] == "monitoring_alert" and source_ref:
            seed_alert = ALERT_SEED_BY_ID.get(source_ref)
            if seed_alert:
                links.append(
                    LinkedItem(
                        type="alert", id=source_ref,
                        label=f"Alert {source_ref} — {seed_alert['description'][:60]}...",
                        href="/monitoring",
                    )
                )
        elif seed["source_type"] == "recon_break" and source_ref:
            links.append(
                LinkedItem(type="break", id=source_ref, label=f"Break {source_ref}", href="/reconciliation")
            )
        linked_items[case_id] = links

        cases.append(
            Case(
                case_id=case_id,
                title=seed["title"],
                description=seed["description"],
                status=status,
                severity=seed["severity"],
                jurisdiction=seed["jurisdiction"],
                vendor=seed["vendor"],
                case_type=seed["case_type"],
                owner=seed["owner"],
                source_type=seed["source_type"],
                source_ref=source_ref,
                resolution_type=resolution_type,
                resolution_note=resolution_note,
                created_at=created_at,
                updated_at=updated_at,
                closed_at=closed_at,
            )
        )

    cases.sort(key=lambda c: c.created_at, reverse=True)
    return cases, timelines, comments, linked_items


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------


def generate_notifications(now: datetime) -> list[Notification]:
    seed = [
        ("alert_fired", "New critical alert: EMIR Trade Report volume anomaly", "Record count 40% below trailing average.", "/monitoring", 5, False),
        ("case_assigned", "Case INC-2852 assigned to you", "EMIR Trade Report volume anomaly — 40% below trailing average", "/cases/INC-2852", 5, False),
        ("recon_completed", "EMIR Trade Recon run completed", "5 breaks found, match rate 99.97%.", "/reconciliation", 70, False),
        ("alert_fired", "Cappitech feed delay detected", "21 minutes late against a 15-minute cadence.", "/monitoring", 40, True),
        ("report_submitted", "MiFID II Transaction Report submitted", "Acknowledged by UnaVista, SLA met.", "/monitoring", 130, True),
        ("case_assigned", "Case INC-2861 assigned to you", "Duplicate trade suspected in MAS position feed.", "/cases/INC-2861", 180, True),
        ("recon_completed", "ASIC Derivative Transaction Recon run completed", "4 breaks found, match rate 99.98%.", "/reconciliation", 210, True),
        ("report_submitted", "FCA Transaction Report submitted", "Acknowledged by Cappitech, SLA met.", "/monitoring", 320, True),
    ]
    out = []
    for idx, (ntype, title, body, link, minutes_ago, read) in enumerate(seed):
        out.append(
            Notification(
                id=f"NTF-{idx + 1:03d}",
                type=ntype,
                title=title,
                body=body,
                link=link,
                read=read,
                created_at=now - timedelta(minutes=minutes_ago),
            )
        )
    return out


# ---------------------------------------------------------------------------
# Overnight briefing (fallback text; ai.py generates the real mock version)
# ---------------------------------------------------------------------------

FALLBACK_BRIEFING = "Briefing generation failed. Check monitoring for overnight status."
