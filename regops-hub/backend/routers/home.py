from fastapi import APIRouter, Depends

from backend.deps import get_current_user
from backend.models.home import HomeSummary, OpenCasesSummary, ReconSummaryRow
from backend.models.notifications import CurrentUser
from backend.services import delta, lakebase

router = APIRouter(prefix="/api/home", tags=["home"])


@router.get("", response_model=HomeSummary)
async def get_home_summary(current_user: CurrentUser = Depends(get_current_user)) -> HomeSummary:
    # Lakebase and Delta are queried independently and merged here in
    # application code, per the consistency contract (never join across
    # the two stores in a single query).
    briefing_text, briefing_time = await lakebase.get_latest_briefing()
    report_status = await lakebase.get_today_submissions_cache()
    feed_status = await delta.get_feed_status()
    active_alerts = await lakebase.get_active_alerts_cache()
    recon_runs = await delta.get_recon_runs()
    my_open_cases = await lakebase.get_cases(owner=current_user.display_name, status_filter="open")

    recon_summary = [
        ReconSummaryRow(
            recon_set_name=r.recon_set_name,
            jurisdiction=r.jurisdiction,
            break_count=r.open_break_count,
            match_rate=r.match_rate,
            status="clean" if r.open_break_count == 0 else "breaks",
            run_id=r.run_id,
        )
        for r in recon_runs
    ]

    return HomeSummary(
        overnight_summary=briefing_text,
        briefing_generated_at=briefing_time,
        report_status=report_status,
        feed_status=feed_status,
        recon_summary=recon_summary,
        active_alerts=active_alerts,
        open_cases=OpenCasesSummary(count=len(my_open_cases), cases=my_open_cases[:5]),
    )
