from datetime import datetime
from typing import Literal

from backend.models.cases import Case
from backend.models.common import CamelModel, Jurisdiction
from backend.models.monitoring import Alert, FeedStatusItem, ReportSubmission


class ReconSummaryRow(CamelModel):
    recon_set_name: str
    jurisdiction: Jurisdiction
    break_count: int
    match_rate: float
    status: Literal["clean", "breaks"]
    run_id: str


class OpenCasesSummary(CamelModel):
    count: int
    cases: list[Case]


class HomeSummary(CamelModel):
    overnight_summary: str
    briefing_generated_at: datetime
    report_status: list[ReportSubmission]
    feed_status: list[FeedStatusItem]
    recon_summary: list[ReconSummaryRow]
    active_alerts: list[Alert]
    open_cases: OpenCasesSummary
