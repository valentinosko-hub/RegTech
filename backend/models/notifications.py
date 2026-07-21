from datetime import datetime
from typing import Literal

from backend.models.common import CamelModel

NotificationType = Literal[
    "alert_fired", "case_assigned", "report_submitted", "recon_completed"
]


class Notification(CamelModel):
    id: str
    type: NotificationType
    title: str
    body: str | None = None
    link: str | None = None
    read: bool
    created_at: datetime


class SavedViewCounts(CamelModel):
    todays_reports: int
    todays_reconciliation: int
    todays_breaks: int
    active_alerts: int
    my_open_cases: int
    awaiting_vendor: int
    late_reports: int


class CurrentUser(CamelModel):
    id: str
    display_name: str
    email: str
    role: Literal["analyst", "lead", "admin"]


class SearchResult(CamelModel):
    type: Literal["case", "run", "alert"]
    id: str
    label: str
    sublabel: str
    href: str
