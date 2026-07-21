import { useNavigate } from 'react-router-dom';

import { ReportStatusPill } from '@/components/shared/StatusBadge';
import { formatTime } from '@/lib/format';
import type { ReportSubmission } from '@/types';

interface ReportTimelineProps {
  reports: ReportSubmission[];
  linkToMonitoring?: boolean;
}

export function ReportTimeline({ reports, linkToMonitoring }: ReportTimelineProps) {
  const navigate = useNavigate();

  if (reports.length === 0) {
    return <p className="py-6 text-center text-sm text-ink-faint">No reports scheduled today.</p>;
  }

  return (
    <ol className="flex flex-col">
      {reports.map((report) => (
        <li
          key={report.submissionId}
          onClick={linkToMonitoring ? () => navigate('/monitoring?tab=reports') : undefined}
          className={`flex items-start gap-4 border-b border-surface-muted/70 py-3 last:border-0 ${
            linkToMonitoring ? 'cursor-pointer hover:bg-surface-subtle' : ''
          }`}
        >
          <div className="w-14 shrink-0 pt-0.5 text-xs font-medium text-ink-faint">{formatTime(report.dueTime)}</div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-ink">{report.reportName}</span>
              <span className="rounded bg-surface-muted px-1.5 py-0.5 text-[10px] font-semibold text-ink-muted">
                {report.jurisdiction}
              </span>
            </div>
            {report.errorMessage && <p className="mt-0.5 text-xs text-status-bad">{report.errorMessage}</p>}
          </div>
          <div className="flex shrink-0 flex-col items-end gap-1 pt-0.5">
            <ReportStatusPill status={report.status} slaState={report.slaState} />
            {report.slaState === 'at_risk' && report.estimatedCompletion && (
              <span className="text-[11px] text-status-warn">Est. {formatTime(report.estimatedCompletion)}</span>
            )}
            {report.slaState === 'on_track' && <span className="text-[11px] text-ink-faint">On track</span>}
          </div>
        </li>
      ))}
    </ol>
  );
}
