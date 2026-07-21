import { DataTable, type DataTableColumn } from '@/components/shared/DataTable';
import { FeedHealthPill } from '@/components/shared/StatusBadge';
import { formatRelative } from '@/lib/format';
import type { FeedStatusItem } from '@/types';

export function FeedStatus({ feeds }: { feeds: FeedStatusItem[] }) {
  const columns: DataTableColumn<FeedStatusItem>[] = [
    { key: 'vendor', header: 'Vendor', render: (f) => <span className="font-medium text-ink">{f.vendor}</span> },
    { key: 'status', header: 'Status', render: (f) => <FeedHealthPill status={f.status} /> },
    { key: 'lastReceived', header: 'Last Received', render: (f) => formatRelative(f.lastReceivedAt) },
    { key: 'cadence', header: 'Expected Cadence', render: (f) => `${f.expectedCadenceMinutes} min` },
    {
      key: 'delay',
      header: 'Delay',
      render: (f) => (f.delayMinutes > 0 ? <span className="text-status-warn">{f.delayMinutes} min</span> : '—'),
    },
  ];

  return <DataTable columns={columns} rows={feeds} rowKey={(f) => f.vendor} emptyMessage="No feed data." />;
}
