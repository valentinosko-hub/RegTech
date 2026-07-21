import { useNavigate } from 'react-router-dom';

import { AlertSeverityBadge } from '@/components/shared/StatusBadge';
import { SlidePanel } from '@/components/shared/SlidePanel';
import { formatDateTime } from '@/lib/format';
import { useAlertDetail, useCreateCaseFromAlert } from '@/hooks/useMonitoring';

interface AlertDetailPanelProps {
  eventId: string | null;
  onClose: () => void;
}

export function AlertDetailPanel({ eventId, onClose }: AlertDetailPanelProps) {
  const { data: alert } = useAlertDetail(eventId);
  const createCase = useCreateCaseFromAlert();
  const navigate = useNavigate();

  return (
    <SlidePanel
      open={eventId !== null}
      onClose={onClose}
      title={alert?.eventId ?? 'Alert'}
      subtitle={alert ? formatDateTime(alert.detectedAt) : undefined}
    >
      {!alert ? (
        <p className="text-sm text-ink-faint">Loading…</p>
      ) : (
        <div className="flex flex-col gap-5">
          <div className="flex items-center gap-2">
            <AlertSeverityBadge severity={alert.severity} />
            <span className="rounded bg-surface-muted px-1.5 py-0.5 text-[10px] font-semibold capitalize text-ink-muted">
              {alert.status}
            </span>
          </div>

          <section>
            <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-faint">Description</h3>
            <p className="text-sm text-ink">{alert.description}</p>
          </section>

          {alert.aiAssessment && (
            <section className="rounded-md bg-accent-subtle px-3 py-2.5">
              <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-accent">AI Assessment</h3>
              <p className="text-sm text-ink">{alert.aiAssessment}</p>
            </section>
          )}

          <section>
            <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-faint">Historical Comparison</h3>
            <p className="text-sm text-ink-muted">{alert.historicalSummary}</p>
            <div className="mt-2 flex gap-4">
              <Stat label="Late (30d)" value={String(alert.lateCountLast30Days)} />
              <Stat label="Avg recovery" value={`${alert.avgRecoveryMinutes} min`} />
            </div>
          </section>

          <section>
            <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-faint">Recommended Action</h3>
            <p className="text-sm text-ink-muted">{alert.recommendedAction}</p>
          </section>

          {alert.sourceVendor && (
            <div className="flex gap-4 border-t border-surface-muted pt-3 text-xs text-ink-faint">
              <span>Vendor: {alert.sourceVendor}</span>
              {alert.sourceReport && <span>Report: {alert.sourceReport}</span>}
            </div>
          )}

          <div className="border-t border-surface-muted pt-4">
            {alert.linkedCaseId ? (
              <button
                onClick={() => navigate(`/cases/${alert.linkedCaseId}`)}
                className="w-full rounded-md border border-surface-muted px-3 py-2 text-[13px] font-medium text-ink-muted hover:bg-surface-subtle"
              >
                View Case {alert.linkedCaseId}
              </button>
            ) : (
              <button
                onClick={() =>
                  createCase.mutate(alert.eventId, {
                    onSuccess: (created) => navigate(`/cases/${created.caseId}`),
                  })
                }
                disabled={createCase.isPending}
                className="w-full rounded-md bg-accent px-3 py-2 text-[13px] font-medium text-white hover:bg-accent-hover disabled:opacity-40"
              >
                {createCase.isPending ? 'Creating…' : 'Create Case'}
              </button>
            )}
          </div>
        </div>
      )}
    </SlidePanel>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[11px] text-ink-faint">{label}</div>
      <div className="text-sm font-semibold text-ink">{value}</div>
    </div>
  );
}
