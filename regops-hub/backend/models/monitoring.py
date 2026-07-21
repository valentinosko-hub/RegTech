from datetime import datetime
from typing import Literal

from backend.models.common import CamelModel, Jurisdiction, Vendor

ReportStatusValue = Literal[
    "scheduled",
    "generating",
    "validating",
    "queued",
    "submitted",
    "acknowledged",
    "failed",
    "resubmitted",
]
SlaState = Literal["on_track", "at_risk", "breached", "met"]


class ReportSubmission(CamelModel):
    submission_id: str
    report_name: str
    jurisdiction: Jurisdiction
    reporting_period: str
    status: ReportStatusValue
    due_time: datetime
    started_at: datetime | None = None
    submitted_at: datetime | None = None
    acknowledged_at: datetime | None = None
    sla_met: bool | None = None
    record_count: int | None = None
    error_message: str | None = None
    sla_state: SlaState | None = None
    estimated_completion: datetime | None = None


FeedHealth = Literal["healthy", "delayed", "failed"]


class FeedStatusItem(CamelModel):
    vendor: Vendor
    status: FeedHealth
    last_received_at: datetime
    expected_cadence_minutes: int
    delay_minutes: int


AlertSeverity = Literal["info", "warning", "critical"]
AlertEventType = Literal[
    "feed_delay",
    "feed_failure",
    "volume_anomaly",
    "sla_warning",
    "sla_breach",
    "report_status_change",
]
AlertStatus = Literal["active", "resolved", "escalated"]


class Alert(CamelModel):
    event_id: str
    event_type: AlertEventType
    source_vendor: Vendor | None = None
    source_report: str | None = None
    severity: AlertSeverity
    description: str
    ai_assessment: str | None = None
    status: AlertStatus
    detected_at: datetime
    resolved_at: datetime | None = None


class AlertHistoryPoint(CamelModel):
    date: str
    late_by_minutes: int
    recovery_minutes: int


class AlertDetail(Alert):
    historical_summary: str
    late_count_last30_days: int
    avg_recovery_minutes: int
    recommended_action: str
    history: list[AlertHistoryPoint]
    linked_case_id: str | None = None


class CreateCaseFromAlertRequest(CamelModel):
    title: str | None = None
    severity: str | None = None
