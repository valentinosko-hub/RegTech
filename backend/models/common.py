"""Shared base classes and literal types for API models.

All models use camelCase on the wire (matching src/types/index.ts) while
staying snake_case in Python, via Pydantic's alias generator.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


Jurisdiction = Literal["ASIC", "MiFID", "EMIR", "FCA", "MAS"]
Vendor = Literal["Cappitech", "Kaizen", "UnaVista", "DTCC"]
Severity = Literal["P1", "P2", "P3", "P4"]
CaseStatus = Literal["open", "investigating", "pending_vendor", "closed"]
CaseType = Literal["incident", "task", "query"]
CaseSourceType = Literal["monitoring_alert", "recon_break", "paste", "manual"]
ResolutionType = Literal[
    "mapping_applied", "resolved_with_note", "false_positive", "escalated_to_case"
]

JURISDICTIONS: list[Jurisdiction] = ["ASIC", "MiFID", "EMIR", "FCA", "MAS"]
VENDORS: list[Vendor] = ["Cappitech", "Kaizen", "UnaVista", "DTCC"]
