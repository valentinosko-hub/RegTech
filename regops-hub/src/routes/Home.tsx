import type { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';

import { CaseStatusPill, FeedHealthPill, ReportStatusPill, SeverityDot } from '@/components/shared/StatusBadge';
import { formatDateTime, formatTime } from '@/lib/format';
import { useHomeSummary } from '@/hooks/useHome';

export function Home() {
  const { data, isLoading } = useHomeSummary();
  const navigate = useNavigate();

  if (isLoading || !data) {
    return <div className="p-8 text-sm text-ink-faint">Loading briefing…</div>;
  }

  const problemFeeds = data.feedStatus.filter((f) => f.status !== 'healthy');

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-5 px-8 py-6">
      <div>
        <h1 className="text-lg font-semibold text-ink">Good morning</h1>
        <p className="mt-0.5 text-xs text-ink-faint">Briefing generated {formatDateTime(data.briefingGeneratedAt)}</p>
      </div>

      <Section title="Overnight Summary">
        <p className="text-sm leading-relaxed text-ink-muted">{data.overnightSummary}</p>
      </Section>

      <Section title="Report Status" onViewAll={() => navigate('/monitoring?tab=reports')}>
        <table className="w-full text-sm">
          <tbody>
            {data.reportStatus.map((report) => (
              <tr
                key={report.submissionId}
                onClick={() => navigate('/monitoring?tab=reports')}
                className="cursor-pointer border-b border-surface-muted/70 last:border-0 hover:bg-surface-subtle"
              >
                <td className="py-2 font-medium text-ink">{report.reportName}</td>
                <td className="py-2 text-ink-faint">{report.jurisdiction}</td>
                <td className="py-2">
                  <ReportStatusPill status={report.status} slaState={report.slaState} />
                </td>
                <td className="py-2 text-right text-ink-faint">{formatTime(report.dueTime)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="Feed Status" onViewAll={() => navigate('/monitoring?tab=feeds')}>
        {problemFeeds.length === 0 ? (
          <p className="text-sm font-medium text-status-good">{data.feedStatus.length} feeds healthy ✓</p>
        ) : (
          <ul className="flex flex-col gap-2.5">
            {problemFeeds.map((feed) => (
              <li key={feed.vendor} className="flex items-center justify-between text-sm">
                <span className="font-medium text-ink">{feed.vendor}</span>
                <FeedHealthPill status={feed.status} />
                <span className="text-ink-faint">{feed.delayMinutes} min delay</span>
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Reconciliation Summary" onViewAll={() => navigate('/reconciliation')}>
        <table className="w-full text-sm">
          <tbody>
            {data.reconSummary.map((row) => (
              <tr
                key={row.runId}
                onClick={() => navigate('/reconciliation')}
                className="cursor-pointer border-b border-surface-muted/70 last:border-0 hover:bg-surface-subtle"
              >
                <td className="py-2 font-medium text-ink">{row.reconSetName}</td>
                <td className="py-2 text-ink-faint">{row.jurisdiction}</td>
                <td className="py-2 text-ink-faint">{row.breakCount} breaks</td>
                <td className="py-2 text-ink-faint">{row.matchRate.toFixed(2)}%</td>
                <td className="py-2 text-right">
                  {row.status === 'clean' ? (
                    <span className="text-xs font-medium text-status-good">Clean ✓</span>
                  ) : (
                    <span className="text-xs font-medium text-status-warn">Breaks</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="Active Alerts" onViewAll={() => navigate('/monitoring?tab=alerts')}>
        {data.activeAlerts.length === 0 ? (
          <p className="text-sm font-medium text-status-good">No active alerts ✓</p>
        ) : (
          <ul className="flex flex-col gap-3">
            {data.activeAlerts.map((alert) => (
              <li
                key={alert.eventId}
                onClick={() => navigate('/monitoring?tab=alerts')}
                className="cursor-pointer rounded-md px-1 py-1 hover:bg-surface-subtle"
              >
                <div className="flex items-center gap-2">
                  <SeverityDotForAlert severity={alert.severity} />
                  <span className="text-sm text-ink">{alert.description}</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Open Cases" onViewAll={() => navigate('/cases?filter=mine')}>
        {data.openCases.count === 0 ? (
          <p className="text-sm font-medium text-status-good">No open cases ✓</p>
        ) : (
          <div className="flex flex-col gap-2">
            <p className="text-xs text-ink-faint">{data.openCases.count} open case(s) assigned to you</p>
            {data.openCases.cases.map((c) => (
              <div
                key={c.caseId}
                onClick={() => navigate(`/cases/${c.caseId}`)}
                className="flex cursor-pointer items-center justify-between rounded-md px-1 py-1.5 hover:bg-surface-subtle"
              >
                <div className="flex items-center gap-2">
                  <SeverityDot severity={c.severity} />
                  <span className="font-mono text-xs text-ink-faint">{c.caseId}</span>
                  <span className="text-sm text-ink">{c.title}</span>
                </div>
                <CaseStatusPill status={c.status} />
              </div>
            ))}
          </div>
        )}
      </Section>
    </div>
  );
}

function SeverityDotForAlert({ severity }: { severity: 'info' | 'warning' | 'critical' }) {
  const color = severity === 'critical' ? 'bg-status-bad' : severity === 'warning' ? 'bg-status-warn' : 'bg-status-info';
  return <span className={`inline-block h-2 w-2 shrink-0 rounded-full ${color}`} />;
}

function Section({ title, onViewAll, children }: { title: string; onViewAll?: () => void; children: ReactNode }) {
  return (
    <section className="rounded-lg border border-surface-muted bg-white p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-ink">{title}</h2>
        {onViewAll && (
          <button onClick={onViewAll} className="text-xs font-medium text-accent hover:text-accent-hover">
            View all
          </button>
        )}
      </div>
      {children}
    </section>
  );
}
