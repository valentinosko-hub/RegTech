import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { AlertDetailPanel } from '@/components/monitoring/AlertDetailPanel';
import { AlertList } from '@/components/monitoring/AlertList';
import { FeedStatus } from '@/components/monitoring/FeedStatus';
import { ReportTimeline } from '@/components/monitoring/ReportTimeline';
import { useAlerts, useFeeds, useReports } from '@/hooks/useMonitoring';

type Tab = 'reports' | 'feeds' | 'alerts';
const TABS: { key: Tab; label: string }[] = [
  { key: 'reports', label: 'Report Timeline' },
  { key: 'feeds', label: 'Feed Status' },
  { key: 'alerts', label: 'Alerts' },
];

export function Monitoring() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialTab = (searchParams.get('tab') as Tab) ?? 'reports';
  const [tab, setTab] = useState<Tab>(initialTab);
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const showLateOnly = searchParams.get('late') === '1';

  const { data: reports, isLoading: reportsLoading } = useReports();
  const { data: feeds, isLoading: feedsLoading } = useFeeds();
  const { data: alerts, isLoading: alertsLoading } = useAlerts();

  const visibleReports = useMemo(() => {
    if (!reports) return [];
    if (!showLateOnly) return reports;
    const now = Date.now();
    return reports.filter(
      (r) => new Date(r.dueTime).getTime() < now && r.status !== 'submitted' && r.status !== 'acknowledged'
    );
  }, [reports, showLateOnly]);

  function selectTab(next: Tab) {
    setTab(next);
    const params = new URLSearchParams(searchParams);
    params.set('tab', next);
    params.delete('late');
    setSearchParams(params, { replace: true });
  }

  return (
    <div className="mx-auto max-w-5xl px-8 py-6">
      <h1 className="text-lg font-semibold text-ink">Monitoring</h1>

      <div className="mt-4 flex gap-1 rounded-md bg-surface-muted p-1">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => selectTab(t.key)}
            className={`rounded-md px-3 py-1.5 text-[13px] font-medium transition ${
              tab === t.key ? 'bg-white text-ink shadow-card' : 'text-ink-muted hover:text-ink'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="mt-4 rounded-lg border border-surface-muted bg-white p-4">
        {tab === 'reports' && (
          <>
            {showLateOnly && (
              <div className="mb-3 flex items-center justify-between rounded-md bg-status-warn/10 px-3 py-1.5 text-xs font-medium text-status-warn">
                Showing only late reports
                <button onClick={() => selectTab('reports')} className="font-semibold underline">
                  Clear filter
                </button>
              </div>
            )}
            {reportsLoading ? (
              <p className="py-6 text-center text-sm text-ink-faint">Loading reports…</p>
            ) : (
              <ReportTimeline reports={visibleReports} />
            )}
          </>
        )}

        {tab === 'feeds' &&
          (feedsLoading ? (
            <p className="py-6 text-center text-sm text-ink-faint">Loading feed status…</p>
          ) : (
            <FeedStatus feeds={feeds ?? []} />
          ))}

        {tab === 'alerts' &&
          (alertsLoading ? (
            <p className="py-6 text-center text-sm text-ink-faint">Loading alerts…</p>
          ) : (
            <AlertList alerts={alerts ?? []} onSelect={setSelectedAlertId} />
          ))}
      </div>

      <AlertDetailPanel eventId={selectedAlertId} onClose={() => setSelectedAlertId(null)} />
    </div>
  );
}
