from fastapi import APIRouter, Depends, HTTPException, Query

from backend.deps import get_current_user
from backend.models.cases import (
    AddCommentRequest,
    Case,
    CaseDetail,
    CaseExtraction,
    CloseCaseRequest,
    Comment,
    CreateCaseRequest,
    ExtractRequest,
    UpdateCaseRequest,
)
from backend.models.notifications import CurrentUser
from backend.services import ai, lakebase

router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.get("", response_model=list[Case])
async def list_cases(
    filter: str = Query("all", pattern="^(mine|open|all)$"),
    search: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
) -> list[Case]:
    if filter == "mine":
        return await lakebase.get_cases(owner=current_user.display_name, search=search)
    if filter == "open":
        return await lakebase.get_cases(status_filter="open", search=search)
    return await lakebase.get_cases(search=search)


@router.post("/extract", response_model=CaseExtraction)
async def extract_case(body: ExtractRequest) -> CaseExtraction:
    extraction = await ai.extract_case_entities(body.text)
    if extraction.status == "ok":
        duplicate = await lakebase.find_recent_similar_case(
            jurisdiction=extraction.jurisdiction.value,
            vendor=extraction.vendor.value,
            case_type=extraction.case_type.value or "incident",
        )
        if duplicate is not None:
            extraction.duplicate_warning = {"caseId": duplicate.case_id, "title": duplicate.title}
    return extraction


@router.post("", response_model=Case)
async def create_case(
    body: CreateCaseRequest, current_user: CurrentUser = Depends(get_current_user)
) -> Case:
    return await lakebase.create_case(
        title=body.title,
        description=body.description,
        severity=body.severity,
        jurisdiction=body.jurisdiction,
        vendor=body.vendor,
        case_type=body.case_type,
        owner=current_user.display_name,
        source_type=body.source_type,
        source_ref=body.source_ref,
    )


@router.get("/{case_id}", response_model=CaseDetail)
async def get_case(case_id: str) -> CaseDetail:
    case = await lakebase.get_case_detail(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.patch("/{case_id}", response_model=Case)
async def update_case(
    case_id: str, body: UpdateCaseRequest, current_user: CurrentUser = Depends(get_current_user)
) -> Case:
    case = await lakebase.update_case(
        case_id,
        status=body.status,
        severity=body.severity,
        owner=body.owner,
        actor=current_user.display_name,
    )
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/{case_id}/comments", response_model=Comment)
async def add_comment(
    case_id: str, body: AddCommentRequest, current_user: CurrentUser = Depends(get_current_user)
) -> Comment:
    comment = await lakebase.add_comment(case_id, author=current_user.display_name, body=body.body)
    if comment is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return comment


@router.post("/{case_id}/close", response_model=Case)
async def close_case(
    case_id: str, body: CloseCaseRequest, current_user: CurrentUser = Depends(get_current_user)
) -> Case:
    case = await lakebase.close_case(
        case_id,
        resolution_type=body.resolution_type,
        resolution_note=body.resolution_note,
        actor=current_user.display_name,
    )
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case
