from datetime import datetime
from typing import Any, Literal

from backend.models.common import (
    CamelModel,
    CaseSourceType,
    CaseStatus,
    CaseType,
    Jurisdiction,
    Severity,
    Vendor,
)


class Case(CamelModel):
    case_id: str
    title: str
    description: str | None = None
    status: CaseStatus
    severity: Severity
    jurisdiction: Jurisdiction | None = None
    vendor: Vendor | None = None
    case_type: CaseType
    owner: str
    source_type: CaseSourceType
    source_ref: str | None = None
    resolution_type: str | None = None
    resolution_note: str | None = None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None = None


TimelineEventType = Literal[
    "created",
    "status_changed",
    "severity_changed",
    "comment_added",
    "escalated",
    "closed",
    "linked",
]


class TimelineEvent(CamelModel):
    id: str
    case_id: str
    event_type: TimelineEventType
    actor: str
    description: str
    metadata: dict[str, Any] | None = None
    created_at: datetime


class Comment(CamelModel):
    id: str
    case_id: str
    author: str
    body: str
    created_at: datetime


class LinkedItem(CamelModel):
    type: Literal["alert", "break"]
    id: str
    label: str
    href: str


class CaseDetail(Case):
    timeline: list[TimelineEvent]
    comments: list[Comment]
    linked_items: list[LinkedItem]


FieldConfidence = Literal["confident", "suggested", "unknown"]


class ExtractedStringField(CamelModel):
    value: str | None = None
    confidence: FieldConfidence


class CaseExtraction(CamelModel):
    status: Literal["ok", "failed"]
    title: ExtractedStringField
    severity: ExtractedStringField
    jurisdiction: ExtractedStringField
    vendor: ExtractedStringField
    case_type: ExtractedStringField
    description: ExtractedStringField
    duplicate_warning: dict[str, str] | None = None


class ExtractRequest(CamelModel):
    text: str


class CreateCaseRequest(CamelModel):
    title: str
    description: str | None = None
    severity: Severity
    jurisdiction: Jurisdiction | None = None
    vendor: Vendor | None = None
    case_type: CaseType = "incident"
    source_type: CaseSourceType = "manual"
    source_ref: str | None = None


class UpdateCaseRequest(CamelModel):
    status: CaseStatus | None = None
    severity: Severity | None = None
    owner: str | None = None


class AddCommentRequest(CamelModel):
    body: str


class CloseCaseRequest(CamelModel):
    resolution_type: str
    resolution_note: str
