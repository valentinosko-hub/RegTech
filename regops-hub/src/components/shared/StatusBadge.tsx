import type { AlertSeverity, BreakCategory, FeedHealth, Severity } from '@/types';

const SEVERITY_STYLES: Record<Severity, string> = {
  P1: 'bg-severity-p1/10 text-severity-p1 border-severity-p1/30',
  P2: 'bg-severity-p2/10 text-severity-p2 border-severity-p2/30',
  P3: 'bg-severity-p3/10 text-severity-p3 border-severity-p3/30',
  P4: 'bg-severity-p4/10 text-severity-p4 border-severity-p4/30',
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className={`inline-flex items-center rounded-md border px-1.5 py-0.5 text-[11px] font-semibold ${SEVERITY_STYLES[severity]}`}
    >
      {severity}
    </span>
  );
}

const SEVERITY_DOT_COLORS: Record<Severity, string> = {
  P1: 'bg-severity-p1',
  P2: 'bg-severity-p2',
  P3: 'bg-severity-p3',
  P4: 'bg-severity-p4',
};

export function SeverityDot({ severity }: { severity: Severity }) {
  return <span className={`inline-block h-2 w-2 rounded-full ${SEVERITY_DOT_COLORS[severity]}`} title={severity} />;
}

const ALERT_SEVERITY_STYLES: Record<AlertSeverity, string> = {
  critical: 'bg-status-bad/10 text-status-bad border-status-bad/30',
  warning: 'bg-status-warn/10 text-status-warn border-status-warn/30',
  info: 'bg-status-info/10 text-status-info border-status-info/30',
};

export function AlertSeverityBadge({ severity }: { severity: AlertSeverity }) {
  return (
    <span
      className={`inline-flex items-center rounded-md border px-1.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide ${ALERT_SEVERITY_STYLES[severity]}`}
    >
      {severity}
    </span>
  );
}

const CATEGORY_LABELS: Record<BreakCategory, string> = {
  known_mapping: 'Known Mapping',
  value_mismatch: 'Value Mismatch',
  date_discrepancy: 'Date Discrepancy',
  missing_record: 'Missing Record',
  extra_record: 'Extra Record',
  novel: 'Novel',
};

const CATEGORY_STYLES: Record<BreakCategory, string> = {
  known_mapping: 'bg-blue-50 text-blue-700 border-blue-200',
  value_mismatch: 'bg-orange-50 text-orange-700 border-orange-200',
  date_discrepancy: 'bg-yellow-50 text-yellow-800 border-yellow-200',
  missing_record: 'bg-red-50 text-red-700 border-red-200',
  extra_record: 'bg-red-50 text-red-700 border-red-200',
  novel: 'bg-gray-100 text-gray-600 border-gray-300',
};

export function CategoryBadge({ category }: { category: BreakCategory | null }) {
  if (category === null) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-md border border-dashed border-ink-faint/50 px-2 py-0.5 text-[11px] font-medium text-ink-muted">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent" />
        Categorising&hellip;
      </span>
    );
  }
  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-medium ${CATEGORY_STYLES[category]}`}>
      {CATEGORY_LABELS[category]}
    </span>
  );
}

type DotColor = 'good' | 'warn' | 'bad' | 'info' | 'neutral';
const DOT_COLORS: Record<DotColor, string> = {
  good: 'bg-status-good',
  warn: 'bg-status-warn',
  bad: 'bg-status-bad',
  info: 'bg-status-info',
  neutral: 'bg-status-neutral',
};

export function StatusPill({ color, label }: { color: DotColor; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-medium text-ink">
      <span className={`h-1.5 w-1.5 rounded-full ${DOT_COLORS[color]}`} />
      {label}
    </span>
  );
}

const FEED_HEALTH_LABELS: Record<FeedHealth, { color: DotColor; label: string }> = {
  healthy: { color: 'good', label: 'Healthy' },
  delayed: { color: 'warn', label: 'Delayed' },
  failed: { color: 'bad', label: 'Failed' },
};

export function FeedHealthPill({ status }: { status: FeedHealth }) {
  const { color, label } = FEED_HEALTH_LABELS[status];
  return <StatusPill color={color} label={label} />;
}

export function reportStatusPresentation(
  status: string,
  slaState: string | null
): { color: DotColor; label: string } {
  if (status === 'failed') return { color: 'bad', label: 'Failed' };
  if (status === 'submitted' || status === 'acknowledged') {
    return slaState === 'breached' ? { color: 'warn', label: 'Submitted late' } : { color: 'good', label: 'Submitted' };
  }
  if (status === 'resubmitted') return { color: 'warn', label: 'Resubmitted' };
  if (slaState === 'at_risk') return { color: 'warn', label: 'At risk' };
  if (status === 'scheduled') return { color: 'neutral', label: 'Scheduled' };
  return { color: 'info', label: status.charAt(0).toUpperCase() + status.slice(1) };
}

export function ReportStatusPill({ status, slaState }: { status: string; slaState: string | null }) {
  const { color, label } = reportStatusPresentation(status, slaState);
  return <StatusPill color={color} label={label} />;
}

const CASE_STATUS_LABELS: Record<string, { color: DotColor; label: string }> = {
  open: { color: 'info', label: 'Open' },
  investigating: { color: 'warn', label: 'Investigating' },
  pending_vendor: { color: 'warn', label: 'Pending Vendor' },
  closed: { color: 'neutral', label: 'Closed' },
};

export function CaseStatusPill({ status }: { status: string }) {
  const preset = CASE_STATUS_LABELS[status] ?? { color: 'neutral' as DotColor, label: status };
  return <StatusPill color={preset.color} label={preset.label} />;
}
