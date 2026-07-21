import { AlertSeverityBadge } from '@/components/shared/StatusBadge';
import { formatRelative } from '@/lib/format';
import type { Alert } from '@/types';

interface AlertListProps {
  alerts: Alert[];
  onSelect: (eventId: string) => void;
}

export function AlertList({ alerts, onSelect }: AlertListProps) {
  if (alerts.length === 0) {
    return <p className="py-6 text-center text-sm text-ink-faint">No active alerts ✅</p>;
  }

  return (
    <ul className="flex flex-col">
      {alerts.map((alert) => (
        <li key={alert.eventId} className="border-b border-surface-muted/70 last:border-0">
          <button
            onClick={() => onSelect(alert.eventId)}
            className="flex w-full items-start gap-3 px-1 py-3 text-left hover:bg-surface-subtle"
          >
            <div className="flex flex-1 flex-col gap-1">
              <div className="flex items-center gap-2">
                <AlertSeverityBadge severity={alert.severity} />
                {alert.status !== 'active' && (
                  <span className="rounded bg-surface-muted px-1.5 py-0.5 text-[10px] font-semibold capitalize text-ink-muted">
                    {alert.status}
                  </span>
                )}
                <span className="text-[11px] text-ink-faint">{formatRelative(alert.detectedAt)}</span>
              </div>
              <p className="text-sm text-ink">{alert.description}</p>
              {alert.aiAssessment && <p className="text-xs italic text-ink-muted">{alert.aiAssessment}</p>}
            </div>
          </button>
        </li>
      ))}
    </ul>
  );
}
