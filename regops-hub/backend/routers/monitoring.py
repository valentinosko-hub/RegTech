from fastapi import APIRouter, Depends, HTTPException

from backend.deps import get_current_user
from backend.models.cases import Case
from backend.models.common import Severity
from backend.models.monitoring import Alert, AlertDetail, FeedStatusItem, ReportSubmission
from backend.models.notifications import CurrentUser
from backend.services import delta, lakebase

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

_ALERT_SEVERITY_TO_CASE_SEVERITY: dict[str, Severity] = {
    "critical": "P1",
    "warning": "P2",
    "info": "P3",
}


@router.get("/reports", response_model=list[ReportSubmission])
async def list_reports() -> list[ReportSubmission]:
    return await lakebase.get_today_submissions_cache()


@router.get("/feeds", response_model=list[FeedStatusItem])
async def list_feeds() -> list[FeedStatusItem]:
    return await delta.get_feed_status()


@router.get("/alerts", response_model=list[Alert])
async def list_alerts() -> list[Alert]:
    return await delta.get_recent_alerts()


@router.get("/alerts/{event_id}", response_model=AlertDetail)
async def get_alert(event_id: str) -> AlertDetail:
    alert = await delta.get_alert_detail(event_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts/{event_id}/create-case", response_model=Case)
async def create_case_from_alert(
    event_id: str, current_user: CurrentUser = Depends(get_current_user)
) -> Case:
    alert = await delta.get_alert_detail(event_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    case = await lakebase.create_case(
        title=f"{alert.source_report or alert.event_type.replace('_', ' ').title()}: {alert.description[:80]}",
        description=alert.description,
        severity=_ALERT_SEVERITY_TO_CASE_SEVERITY.get(alert.severity, "P3"),
        jurisdiction=None,
        vendor=alert.source_vendor,
        case_type="incident",
        owner=current_user.display_name,
        source_type="monitoring_alert",
        source_ref=event_id,
    )
    # Write case to Lakebase, then immediately update the alert in Delta —
    # don't wait for the sync round-trip (per the consistency contract).
    await delta.escalate_alert(event_id)
    return case
