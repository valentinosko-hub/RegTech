"""Endpoints backing global shell elements: current-user identity, saved
view badge counts, notifications, and command-bar search. Not one of the
four product modules — this is cross-cutting app-shell plumbing."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from backend.deps import get_current_user
from backend.models.notifications import (
    CurrentUser,
    Notification,
    SavedViewCounts,
    SearchResult,
)
from backend.services import delta, lakebase

router = APIRouter(tags=["shell"])


@router.get("/api/me", response_model=CurrentUser)
async def get_me(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return current_user


@router.get("/api/views/counts", response_model=SavedViewCounts)
async def get_saved_view_counts(current_user: CurrentUser = Depends(get_current_user)) -> SavedViewCounts:
    reports = await lakebase.get_today_submissions_cache()
    breaks = []
    for run in await delta.get_recon_runs():
        breaks.extend(await delta.get_recon_breaks(run.run_id))
    alerts = await lakebase.get_active_alerts_cache()
    my_cases = await lakebase.get_cases(owner=current_user.display_name, status_filter="open")
    vendor_cases = await lakebase.get_cases(status_filter="pending_vendor")
    runs = await delta.get_recon_runs()

    now = datetime.now(timezone.utc)
    late_reports = sum(
        1 for r in reports if r.due_time < now and r.status not in ("submitted", "acknowledged")
    )
    open_breaks = sum(1 for b in breaks if b.status == "open")

    return SavedViewCounts(
        todays_reports=len(reports),
        todays_reconciliation=len(runs),
        todays_breaks=open_breaks,
        active_alerts=len(alerts),
        my_open_cases=len(my_cases),
        awaiting_vendor=len(vendor_cases),
        late_reports=late_reports,
    )


@router.get("/api/notifications", response_model=list[Notification])
async def list_notifications() -> list[Notification]:
    return await lakebase.get_notifications()


@router.post("/api/notifications/{notification_id}/read", response_model=Notification)
async def mark_notification_read(notification_id: str) -> Notification:
    notification = await lakebase.mark_notification_read(notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.post("/api/notifications/read-all")
async def mark_all_notifications_read() -> dict[str, int]:
    count = await lakebase.mark_all_notifications_read()
    return {"updated": count}


@router.get("/api/search", response_model=list[SearchResult])
async def search(q: str = "") -> list[SearchResult]:
    query = q.strip()
    if not query:
        return []
    needle = query.lower()
    results: list[SearchResult] = []

    cases = await lakebase.get_cases(search=query)
    for case in cases[:8]:
        results.append(
            SearchResult(
                type="case",
                id=case.case_id,
                label=f"{case.case_id} — {case.title}",
                sublabel=f"{case.status.replace('_', ' ')} · {case.severity}",
                href=f"/cases/{case.case_id}",
            )
        )

    for run in await delta.get_recon_runs():
        if needle in run.recon_set_name.lower() or needle in run.jurisdiction.lower():
            results.append(
                SearchResult(
                    type="run",
                    id=run.run_id,
                    label=run.recon_set_name,
                    sublabel=f"{run.jurisdiction} · {run.open_break_count} open breaks",
                    href=f"/reconciliation?run={run.run_id}",
                )
            )

    for alert in await delta.get_recent_alerts():
        if needle in alert.description.lower() or (alert.source_vendor and needle in alert.source_vendor.lower()):
            results.append(
                SearchResult(
                    type="alert",
                    id=alert.event_id,
                    label=alert.description[:70],
                    sublabel=f"{alert.severity} · {alert.status}",
                    href="/monitoring",
                )
            )

    return results[:12]
