"""In-memory mutable store standing in for Lakebase + Delta in Phase 1.

Everything below Phase 2/3 will be replaced: `lakebase.py` and `delta.py`
will run real SQL against Postgres / Databricks SQL warehouses instead of
reading/writing this object. The `store` singleton is intentionally the
*only* place that holds mutable state so that swap-over is a single-file
change.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from backend.models.cases import Case, Comment, LinkedItem, TimelineEvent
from backend.models.monitoring import Alert
from backend.models.notifications import Notification
from backend.models.reconciliation import MappingRule, ReconBreak, ReconRun
from backend.services import ai, mock_data

logger = logging.getLogger("regops.mock_store")


class MockStore:
    def __init__(self) -> None:
        self.boot_time: datetime = mock_data.now_utc()

        self.report_submissions = mock_data.generate_report_submissions(self.boot_time)
        self.feed_status = mock_data.generate_feed_status(self.boot_time)

        alerts = mock_data.generate_alerts(self.boot_time)
        self.alerts: dict[str, Alert] = {a.event_id: a for a in alerts}
        self.alert_order: list[str] = [a.event_id for a in alerts]

        runs, breaks, mapping_rules, mapping_by_id = mock_data.generate_recon_data(self.boot_time)
        self.recon_runs: dict[str, ReconRun] = {r.run_id: r for r in runs}
        self.recon_run_order: list[str] = [r.run_id for r in runs]
        self.recon_breaks: dict[str, ReconBreak] = {b.break_id: b for b in breaks}
        self.mapping_rules: dict[str, MappingRule] = mapping_by_id
        self.mapping_rules_list: list[MappingRule] = mapping_rules

        break_link_map = {
            2: self._find_break_id_by_trade("ASX-7724280"),
            10: self._find_break_id_by_trade("MAS-55021"),
        }
        break_link_map = {k: v for k, v in break_link_map.items() if v}

        cases, timelines, comments, linked_items = mock_data.generate_cases(self.boot_time, break_link_map)
        self.cases: dict[str, Case] = {c.case_id: c for c in cases}
        self.case_order: list[str] = [c.case_id for c in cases]
        self.timelines: dict[str, list[TimelineEvent]] = timelines
        self.comments: dict[str, list[Comment]] = comments
        self.linked_items: dict[str, list[LinkedItem]] = linked_items
        self.next_case_num = 2851 + len(cases)

        # Back-link breaks/alerts to the cases that were opened from them.
        self.alert_linked_case: dict[str, str] = {}
        for case in cases:
            if case.source_type == "recon_break" and case.source_ref in self.recon_breaks:
                self.recon_breaks[case.source_ref].linked_case_id = case.case_id
            elif case.source_type == "monitoring_alert" and case.source_ref:
                self.alert_linked_case[case.source_ref] = case.case_id

        notifications = mock_data.generate_notifications(self.boot_time)
        self.notifications: dict[str, Notification] = {n.id: n for n in notifications}
        self.notification_order: list[str] = [n.id for n in notifications]

        self.overnight_summary = self._build_overnight_summary()
        self.briefing_generated_at = self.boot_time - timedelta(hours=1, minutes=12)

        self._background_tasks: set[asyncio.Task] = set()

    # -- lookups -----------------------------------------------------------

    def _find_break_id_by_trade(self, trade_id: str) -> str | None:
        for b in self.recon_breaks.values():
            if b.source_record.get("tradeId") == trade_id:
                return b.break_id
        return None

    def _build_overnight_summary(self) -> str:
        failed = [r for r in self.report_submissions if r.status == "failed"]
        breached = [r for r in self.report_submissions if r.sla_state == "breached"]
        active_alerts = [a for a in self.alerts.values() if a.status == "active"]
        critical_alerts = [a for a in active_alerts if a.severity == "critical"]
        total_breaks = sum(1 for b in self.recon_breaks.values() if b.status == "open")

        if not failed and not breached and not critical_alerts:
            return (
                "Quiet overnight session — all scheduled reports are tracking on time and no critical "
                f"alerts fired. {total_breaks} reconciliation breaks are open across today's runs, in line "
                "with normal volume."
            )

        parts = []
        if failed:
            parts.append(f"{len(failed)} report(s) failed submission and need attention")
        if breached:
            parts.append(f"{len(breached)} report(s) breached SLA but ultimately submitted")
        if critical_alerts:
            parts.append(f"{len(critical_alerts)} critical alert(s) are still active")
        parts.append(f"{total_breaks} reconciliation breaks are open across today's runs")
        return "Overnight summary: " + "; ".join(parts) + "."

    # -- background AI simulation ------------------------------------------

    def schedule_pending_classification(self) -> None:
        for brk in self.recon_breaks.values():
            if brk.category is None:
                task = asyncio.create_task(self._classify_after_delay(brk.break_id))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)

    async def _classify_after_delay(self, break_id: str) -> None:
        await asyncio.sleep(8)
        brk = self.recon_breaks.get(break_id)
        if brk is None:
            return
        try:
            category = await ai.classify_break(brk)
        except Exception:  # noqa: BLE001 - mock job must never crash the app
            logger.exception("break classification failed for %s", break_id)
            category = "novel"
        brk.category = category

    # -- id generation -------------------------------------------------------

    def next_case_id(self) -> str:
        self.next_case_num += 1
        return f"INC-{self.next_case_num}"


store = MockStore()
