from datetime import datetime
from typing import Literal

from backend.models.common import CamelModel, Jurisdiction, ResolutionType

ReconRunStatus = Literal["completed", "reviewed", "signed_off"]


class ReconRun(CamelModel):
    run_id: str
    recon_set_name: str
    jurisdiction: Jurisdiction
    run_date: str
    source_count: int
    target_count: int
    matched_count: int
    break_count: int
    open_break_count: int
    match_rate: float
    status: ReconRunStatus
    reviewed_by: str | None = None
    signed_off_at: datetime | None = None


BreakCategory = Literal[
    "known_mapping",
    "value_mismatch",
    "date_discrepancy",
    "missing_record",
    "extra_record",
    "novel",
]
BreakStatus = Literal["open", "resolved", "escalated"]


class ReconBreak(CamelModel):
    break_id: str
    run_id: str
    recon_set_name: str
    jurisdiction: Jurisdiction
    field_name: str
    source_value: str
    target_value: str
    source_record: dict[str, str]
    target_record: dict[str, str]
    category: BreakCategory | None = None
    historical_frequency: int
    ai_explanation: str | None = None
    status: BreakStatus
    resolution_type: ResolutionType | None = None
    resolution_note: str | None = None
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    linked_case_id: str | None = None
    linked_mapping_rule_id: str | None = None
    created_at: datetime


class MappingRule(CamelModel):
    id: str
    field_pattern: str
    source_pattern: str
    target_pattern: str
    resolution_description: str


class ResolveBreakRequest(CamelModel):
    resolution_type: ResolutionType
    note: str | None = None
    mapping_rule_id: str | None = None


class BulkResolveRequest(CamelModel):
    break_ids: list[str]
    resolution_type: ResolutionType
    note: str | None = None
    mapping_rule_id: str | None = None


class BulkResolveResult(CamelModel):
    updated: list[ReconBreak]
    failed_break_ids: list[str]


class SignOffResult(CamelModel):
    run: ReconRun
