"""Lakebase (Postgres) data access.

Phase 1: every function below reads/writes `mock_store.store` in memory.
Phase 2: replace the body of each function with an asyncpg query against
`LAKEBASE_CONNECTION_STRING`, keeping the exact same signature and return
types (the Pydantic models in backend/models/). Routers and the frontend
never need to change.

Owns: cases, timeline_events, comments, notifications, mapping_rules,
briefings, and the `active_alerts` / `today_submissions` read caches that
are synced from Delta.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from backend.models.cases import Case, CaseDetail, Comment, LinkedItem, TimelineEvent
from backend.models.monitoring import Alert, ReportSubmission
from backend.models.notifications import Notification
from backend.models.reconciliation import MappingRule
from backend.services.mock_store import store

DB_TIMEOUT_SECONDS = 3


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------


async def get_cases(owner: str | None = None, status_filter: str | None = None, search: str | None = None) -> list[Case]:
    await asyncio.sleep(0)  # Phase 2: await asyncpg pool.fetch(...)
    cases = [store.cases[cid] for cid in store.case_order]
    if owner:
        cases = [c for c in cases if c.owner == owner]
    if status_filter == "open":
        cases = [c for c in cases if c.status != "closed"]
    elif status_filter and status_filter != "all":
        cases = [c for c in cases if c.status == status_filter]
    if search:
        needle = search.lower()
        cases = [
            c
            for c in cases
            if needle in c.case_id.lower() or needle in c.title.lower() or needle in (c.description or "").lower()
        ]
    return cases


async def get_case_detail(case_id: str) -> CaseDetail | None:
    await asyncio.sleep(0)
    case = store.cases.get(case_id)
    if case is None:
        return None
    return CaseDetail(
        **case.model_dump(by_alias=False),
        timeline=store.timelines.get(case_id, []),
        comments=store.comments.get(case_id, []),
        linked_items=store.linked_items.get(case_id, []),
    )


async def create_case(
    *,
    title: str,
    description: str | None,
    severity: str,
    jurisdiction: str | None,
    vendor: str | None,
    case_type: str,
    owner: str,
    source_type: str,
    source_ref: str | None,
) -> Case:
    await asyncio.sleep(0)  # Phase 2: INSERT INTO cases ... RETURNING *
    case_id = store.next_case_id()
    now = datetime.now(timezone.utc)
    case = Case(
        case_id=case_id,
        title=title,
        description=description,
        status="open",
        severity=severity,  # type: ignore[arg-type]
        jurisdiction=jurisdiction,  # type: ignore[arg-type]
        vendor=vendor,  # type: ignore[arg-type]
        case_type=case_type,  # type: ignore[arg-type]
        owner=owner,
        source_type=source_type,  # type: ignore[arg-type]
        source_ref=source_ref,
        resolution_type=None,
        resolution_note=None,
        created_at=now,
        updated_at=now,
        closed_at=None,
    )
    store.cases[case_id] = case
    store.case_order.insert(0, case_id)
    store.timelines[case_id] = [
        TimelineEvent(
            id=f"{case_id}-EVT1",
            case_id=case_id,
            event_type="created",
            actor=owner,
            description=f"Case created from {source_type.replace('_', ' ')}.",
            metadata={"sourceRef": source_ref} if source_ref else None,
            created_at=now,
        )
    ]
    store.comments[case_id] = []
    links: list[LinkedItem] = []
    if source_type == "monitoring_alert" and source_ref:
        links.append(LinkedItem(type="alert", id=source_ref, label=f"Alert {source_ref}", href="/monitoring"))
        store.alert_linked_case[source_ref] = case_id
    elif source_type == "recon_break" and source_ref:
        links.append(LinkedItem(type="break", id=source_ref, label=f"Break {source_ref}", href="/reconciliation"))
        if source_ref in store.recon_breaks:
            store.recon_breaks[source_ref].linked_case_id = case_id
    store.linked_items[case_id] = links
    return case


async def update_case(case_id: str, *, status: str | None, severity: str | None, owner: str | None, actor: str) -> Case | None:
    await asyncio.sleep(0)  # Phase 2: UPDATE cases SET ... WHERE case_id = $1
    case = store.cases.get(case_id)
    if case is None:
        return None
    now = datetime.now(timezone.utc)
    events = store.timelines.setdefault(case_id, [])
    if status and status != case.status:
        case.status = status  # type: ignore[assignment]
        events.append(
            TimelineEvent(
                id=f"{case_id}-EVT{len(events) + 1}",
                case_id=case_id,
                event_type="status_changed",
                actor=actor,
                description=f"Status changed to {status.replace('_', ' ')}.",
                metadata={"status": status},
                created_at=now,
            )
        )
    if severity and severity != case.severity:
        case.severity = severity  # type: ignore[assignment]
        events.append(
            TimelineEvent(
                id=f"{case_id}-EVT{len(events) + 1}",
                case_id=case_id,
                event_type="severity_changed",
                actor=actor,
                description=f"Severity changed to {severity}.",
                metadata={"severity": severity},
                created_at=now,
            )
        )
    if owner and owner != case.owner:
        case.owner = owner
    case.updated_at = now
    return case


async def close_case(case_id: str, *, resolution_type: str, resolution_note: str, actor: str) -> Case | None:
    await asyncio.sleep(0)
    case = store.cases.get(case_id)
    if case is None:
        return None
    now = datetime.now(timezone.utc)
    case.status = "closed"
    case.resolution_type = resolution_type
    case.resolution_note = resolution_note
    case.closed_at = now
    case.updated_at = now
    events = store.timelines.setdefault(case_id, [])
    events.append(
        TimelineEvent(
            id=f"{case_id}-EVT{len(events) + 1}",
            case_id=case_id,
            event_type="closed",
            actor=actor,
            description=resolution_note,
            metadata={"resolutionType": resolution_type},
            created_at=now,
        )
    )
    return case


async def add_comment(case_id: str, *, author: str, body: str) -> Comment | None:
    await asyncio.sleep(0)  # Phase 2: INSERT INTO comments ... RETURNING *
    if case_id not in store.cases:
        return None
    now = datetime.now(timezone.utc)
    comment_list = store.comments.setdefault(case_id, [])
    comment = Comment(id=f"{case_id}-CMT{len(comment_list) + 1}", case_id=case_id, author=author, body=body, created_at=now)
    comment_list.append(comment)
    events = store.timelines.setdefault(case_id, [])
    events.append(
        TimelineEvent(
            id=f"{case_id}-EVT{len(events) + 1}",
            case_id=case_id,
            event_type="comment_added",
            actor=author,
            description="Added a comment.",
            metadata=None,
            created_at=now,
        )
    )
    store.cases[case_id].updated_at = now
    return comment


async def find_recent_similar_case(*, jurisdiction: str | None, vendor: str | None, case_type: str) -> Case | None:
    """Lightweight duplicate-detection used by paste-to-case. Not part of the
    AI extraction call — a separate Lakebase lookup, per the consistency
    contract (AI output and DB dedup checks are independent concerns)."""
    await asyncio.sleep(0)
    for case_id in store.case_order:
        case = store.cases[case_id]
        if case.status == "closed":
            continue
        if case.case_type == case_type and jurisdiction and case.jurisdiction == jurisdiction and vendor and case.vendor == vendor:
            return case
    return None


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------


async def get_notifications() -> list[Notification]:
    await asyncio.sleep(0)
    return [store.notifications[nid] for nid in store.notification_order]


async def mark_notification_read(notification_id: str) -> Notification | None:
    await asyncio.sleep(0)
    notification = store.notifications.get(notification_id)
    if notification is None:
        return None
    notification.read = True
    return notification


async def mark_all_notifications_read() -> int:
    await asyncio.sleep(0)
    count = 0
    for notification in store.notifications.values():
        if not notification.read:
            notification.read = True
            count += 1
    return count


# ---------------------------------------------------------------------------
# Mapping rules
# ---------------------------------------------------------------------------


async def get_mapping_rules() -> list[MappingRule]:
    await asyncio.sleep(0)
    return store.mapping_rules_list


async def get_mapping_rule(mapping_rule_id: str) -> MappingRule | None:
    await asyncio.sleep(0)
    return store.mapping_rules.get(mapping_rule_id)


# ---------------------------------------------------------------------------
# Synced caches (active_alerts / today_submissions) — mirror Delta, <30s lag
# ---------------------------------------------------------------------------


async def get_active_alerts_cache() -> list[Alert]:
    await asyncio.sleep(0)
    return [store.alerts[eid] for eid in store.alert_order if store.alerts[eid].status == "active"]


async def get_today_submissions_cache() -> list[ReportSubmission]:
    await asyncio.sleep(0)
    return store.report_submissions


# ---------------------------------------------------------------------------
# Briefings
# ---------------------------------------------------------------------------


async def get_latest_briefing() -> tuple[str, datetime]:
    await asyncio.sleep(0)
    return store.overnight_summary, store.briefing_generated_at
