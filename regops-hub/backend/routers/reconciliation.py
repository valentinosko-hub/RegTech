from fastapi import APIRouter, Depends, HTTPException

from backend.deps import get_current_user
from backend.models.cases import Case
from backend.models.notifications import CurrentUser
from backend.models.reconciliation import (
    BulkResolveRequest,
    BulkResolveResult,
    MappingRule,
    ReconBreak,
    ReconRun,
    ResolveBreakRequest,
    SignOffResult,
)
from backend.services import ai, delta, lakebase

router = APIRouter(prefix="/api/reconciliation", tags=["reconciliation"])


@router.get("/runs", response_model=list[ReconRun])
async def list_runs() -> list[ReconRun]:
    return await delta.get_recon_runs()


@router.get("/mapping-rules", response_model=list[MappingRule])
async def list_mapping_rules() -> list[MappingRule]:
    return await lakebase.get_mapping_rules()


@router.get("/runs/{run_id}/breaks", response_model=list[ReconBreak])
async def list_breaks(run_id: str) -> list[ReconBreak]:
    run = await delta.get_recon_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Recon run not found")
    return await delta.get_recon_breaks(run_id)


@router.get("/breaks/{break_id}", response_model=ReconBreak)
async def get_break(break_id: str) -> ReconBreak:
    brk = await delta.get_break(break_id)
    if brk is None:
        raise HTTPException(status_code=404, detail="Break not found")
    if brk.ai_explanation is None and brk.category is not None:
        mapping_rule = (
            await lakebase.get_mapping_rule(brk.linked_mapping_rule_id) if brk.linked_mapping_rule_id else None
        )
        explanation = await ai.explain_break(brk, mapping_rule)
        await delta.cache_break_explanation(break_id, explanation)
        brk = await delta.get_break(break_id)
    return brk


@router.post("/breaks/{break_id}/resolve", response_model=ReconBreak)
async def resolve_break(
    break_id: str, body: ResolveBreakRequest, current_user: CurrentUser = Depends(get_current_user)
) -> ReconBreak:
    result = await delta.resolve_break(
        break_id,
        resolution_type=body.resolution_type,
        note=body.note,
        mapping_rule_id=body.mapping_rule_id,
        actor=current_user.display_name,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Break not found")
    return result


@router.post("/breaks/bulk-resolve", response_model=BulkResolveResult)
async def bulk_resolve_breaks(
    body: BulkResolveRequest, current_user: CurrentUser = Depends(get_current_user)
) -> BulkResolveResult:
    return await delta.bulk_resolve_breaks(
        body.break_ids,
        resolution_type=body.resolution_type,
        note=body.note,
        mapping_rule_id=body.mapping_rule_id,
        actor=current_user.display_name,
    )


@router.post("/runs/{run_id}/sign-off", response_model=SignOffResult)
async def sign_off_run(run_id: str, current_user: CurrentUser = Depends(get_current_user)) -> SignOffResult:
    run = await delta.sign_off_run(run_id, reviewed_by=current_user.display_name)
    if run is None:
        raise HTTPException(status_code=404, detail="Recon run not found")
    return SignOffResult(run=run)


@router.post("/breaks/{break_id}/create-case", response_model=Case)
async def create_case_from_break(
    break_id: str, current_user: CurrentUser = Depends(get_current_user)
) -> Case:
    brk = await delta.get_break(break_id)
    if brk is None:
        raise HTTPException(status_code=404, detail="Break not found")

    severity = "P2" if brk.category in ("missing_record", "novel") else "P3"
    case = await lakebase.create_case(
        title=f"Recon break on {brk.recon_set_name}: {brk.field_name} mismatch ({brk.break_id})",
        description=brk.ai_explanation
        or f"{brk.field_name}: source={brk.source_value} vs target={brk.target_value}",
        severity=severity,
        jurisdiction=brk.jurisdiction,
        vendor=None,
        case_type="incident",
        owner=current_user.display_name,
        source_type="recon_break",
        source_ref=break_id,
    )
    await delta.resolve_break(
        break_id,
        resolution_type="escalated_to_case",
        note=f"Escalated to case {case.case_id}.",
        mapping_rule_id=None,
        actor=current_user.display_name,
    )
    await delta.link_break_to_case(break_id, case.case_id)
    return case
