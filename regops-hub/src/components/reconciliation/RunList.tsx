import { DataTable, type DataTableColumn } from '@/components/shared/DataTable';
import { StatusPill } from '@/components/shared/StatusBadge';
import type { ReconRun } from '@/types';

interface RunListProps {
  runs: ReconRun[];
  onSelect: (runId: string) => void;
}

export function RunList({ runs, onSelect }: RunListProps) {
  const columns: DataTableColumn<ReconRun>[] = [
    {
      key: 'reconSetName',
      header: 'Recon Set',
      render: (r) => (
        <div>
          <div className="font-medium text-ink">{r.reconSetName}</div>
          <div className="text-[11px] text-ink-faint">{r.jurisdiction}</div>
        </div>
      ),
    },
    { key: 'sourceCount', header: 'Source Count', className: 'text-right', render: (r) => r.sourceCount.toLocaleString() },
    { key: 'targetCount', header: 'Target Count', className: 'text-right', render: (r) => r.targetCount.toLocaleString() },
    {
      key: 'breakCount',
      header: 'Breaks',
      className: 'text-right',
      render: (r) => (
        <span className={r.openBreakCount > 0 ? 'font-semibold text-status-warn' : 'text-ink-faint'}>
          {r.openBreakCount}
        </span>
      ),
    },
    { key: 'matchRate', header: 'Match Rate', className: 'text-right', render: (r) => `${r.matchRate.toFixed(2)}%` },
    {
      key: 'status',
      header: 'Status',
      render: (r) =>
        r.status === 'signed_off' ? (
          <StatusPill color="good" label="Signed Off" />
        ) : r.openBreakCount === 0 ? (
          <StatusPill color="good" label="Clean" />
        ) : (
          <StatusPill color="warn" label="Breaks" />
        ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      rows={runs}
      rowKey={(r) => r.runId}
      onRowClick={(r) => onSelect(r.runId)}
      emptyMessage="No reconciliation runs today."
    />
  );
}
