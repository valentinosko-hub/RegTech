"""Delta Lake data access (queried via Databricks SQL warehouse).

Phase 1: every function below reads/writes `mock_store.store` in memory.
Phase 3: replace the body of each function with a databricks-sql-connector
query against `regtech_ops.operational.*`, keeping the exact same
signature and return types. Routers and the frontend never need to change.

Owns: monitoring_events (alerts, feed health), report_submissions,
recon_runs, recon_breaks, ai_generations.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from backend.models.monitoring import Alert, AlertDetail, FeedStatusItem, ReportSubmission
from backend.models.reconciliation import BulkResolveResult, ReconBreak, ReconRun
from backend.services import mock_data
from backend.services.mock_store import store

WAREHOUSE_TIMEOUT_SECONDS = 8


# ---------------------------------------------------------------------------
# Monitoring: report submissions, feed status
# ---------------------------------------------------------------------------


async def get_report_submissions() -> list[ReportSubmission]:
    await asyncio.sleep(0)  # Phase 3: SELECT ... FROM report_submissions WHERE reporting_period = current_date()
    return store.report_submissions


async def get_feed_status() -> list[FeedStatusItem]:
    await asyncio.sleep(0)
    return store.feed_status


# ---------------------------------------------------------------------------
# Monitoring: alerts (monitoring_events)
# ---------------------------------------------------------------------------


async def get_recent_alerts() -> list[Alert]:
    """Broader alert list (active + recently resolved/escalated) for the
    Monitoring > Alerts tab, which needs more context than the Lakebase
    `active_alerts` cache alone provides."""
    await asyncio.sleep(0)
    return [store.alerts[eid] for eid in store.alert_order]


async def get_alert_detail(event_id: str) -> AlertDetail | None:
    await asyncio.sleep(0)
    alert = store.alerts.get(event_id)
    if alert is None:
        return None
    seed = mock_data.ALERT_SEED_BY_ID.get(event_id, {})
    history = mock_data.alert_history(store.boot_time, seed) if seed else []
    late_count = seed.get("late_count", 0)
    avg_recovery = seed.get("avg_recovery", 0)
    return AlertDetail(
        **alert.model_dump(by_alias=False),
        historical_summary=(
            f"Late {late_count} times in the last 30 days, average recovery {avg_recovery} minutes."
        ),
        late_count_last30_days=late_count,
        avg_recovery_minutes=avg_recovery,
        recommended_action=seed.get("recommended_action", "Monitor and re-check at next polling interval."),
        history=history,
        linked_case_id=store.alert_linked_case.get(event_id),
    )


async def escalate_alert(event_id: str) -> Alert | None:
    """Called immediately (not waiting for sync) when a case is created
    from an alert, per the consistency contract."""
    await asyncio.sleep(0)
    alert = store.alerts.get(event_id)
    if alert is None:
        return None
    alert.status = "escalated"
    alert.resolved_at = datetime.now(timezone.utc)
    return alert


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------


async def get_recon_runs() -> list[ReconRun]:
    await asyncio.sleep(0)  # Phase 3: SELECT ... FROM recon_runs WHERE run_date = current_date()
    return [store.recon_runs[rid] for rid in store.recon_run_order]


async def get_recon_run(run_id: str) -> ReconRun | None:
    await asyncio.sleep(0)
    return store.recon_runs.get(run_id)


async def get_recon_breaks(run_id: str) -> list[ReconBreak]:
    await asyncio.sleep(0)
    return [b for b in store.recon_breaks.values() if b.run_id == run_id]


async def get_break(break_id: str) -> ReconBreak | None:
    await asyncio.sleep(0)
    return store.recon_breaks.get(break_id)


def _recompute_run_counts(run_id: str) -> None:
    run = store.recon_runs.get(run_id)
    if run is None:
        return
    breaks = [b for b in store.recon_breaks.values() if b.run_id == run_id]
    run.open_break_count = sum(1 for b in breaks if b.status == "open")


async def resolve_break(
    break_id: str,
    *,
    resolution_type: str,
    note: str | None,
    mapping_rule_id: str | None,
    actor: str,
) -> ReconBreak | None:
    await asyncio.sleep(0)  # Phase 3: UPDATE recon_breaks SET ... WHERE break_id = $1
    brk = store.recon_breaks.get(break_id)
    if brk is None:
        return None
    brk.status = "resolved" if resolution_type != "escalated_to_case" else "escalated"
    brk.resolution_type = resolution_type  # type: ignore[assignment]
    brk.resolution_note = note
    brk.resolved_by = actor
    brk.resolved_at = datetime.now(timezone.utc)
    if mapping_rule_id:
        brk.linked_mapping_rule_id = mapping_rule_id
    _recompute_run_counts(brk.run_id)
    return brk


async def bulk_resolve_breaks(
    break_ids: list[str],
    *,
    resolution_type: str,
    note: str | None,
    mapping_rule_id: str | None,
    actor: str,
) -> BulkResolveResult:
    updated: list[ReconBreak] = []
    failed: list[str] = []
    for break_id in break_ids:
        result = await resolve_break(
            break_id,
            resolution_type=resolution_type,
            note=note,
            mapping_rule_id=mapping_rule_id,
            actor=actor,
        )
        if result is None:
            failed.append(break_id)
        else:
            updated.append(result)
    return BulkResolveResult(updated=updated, failed_break_ids=failed)


async def link_break_to_case(break_id: str, case_id: str) -> None:
    brk = store.recon_breaks.get(break_id)
    if brk is not None:
        brk.linked_case_id = case_id


async def sign_off_run(run_id: str, *, reviewed_by: str) -> ReconRun | None:
    await asyncio.sleep(0)
    run = store.recon_runs.get(run_id)
    if run is None:
        return None
    run.status = "signed_off"
    run.reviewed_by = reviewed_by
    run.signed_off_at = datetime.now(timezone.utc)
    return run


async def cache_break_explanation(break_id: str, explanation: str) -> None:
    """Persist the AI explanation so it is never regenerated for the same
    break (per Call 3's caching rule)."""
    brk = store.recon_breaks.get(break_id)
    if brk is not None:
        brk.ai_explanation = explanation
