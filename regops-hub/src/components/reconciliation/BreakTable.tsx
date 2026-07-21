import { DataTable, type DataTableColumn } from '@/components/shared/DataTable';
import { CategoryBadge } from '@/components/shared/StatusBadge';
import type { ReconBreak } from '@/types';

interface BreakTableProps {
  breaks: ReconBreak[];
  onSelect: (breakId: string) => void;
  selectedKeys: Set<string>;
  onToggleSelect: (breakId: string) => void;
}

export function BreakTable({ breaks, onSelect, selectedKeys, onToggleSelect }: BreakTableProps) {
  const columns: DataTableColumn<ReconBreak>[] = [
    { key: 'breakId', header: 'Break ID', render: (b) => <span className="font-mono text-xs">{b.breakId}</span> },
    { key: 'field', header: 'Field', render: (b) => <span className="font-medium text-ink">{b.fieldName}</span> },
    {
      key: 'source',
      header: 'Source Value',
      render: (b) => <span className="font-mono text-xs text-ink-muted">{b.sourceValue}</span>,
    },
    {
      key: 'target',
      header: 'Target Value',
      render: (b) => <span className="font-mono text-xs text-ink-muted">{b.targetValue}</span>,
    },
    { key: 'category', header: 'Category', render: (b) => <CategoryBadge category={b.category} /> },
    {
      key: 'frequency',
      header: 'History',
      className: 'text-right',
      render: (b) => (b.historicalFrequency > 0 ? `×${b.historicalFrequency}` : 'New'),
    },
    {
      key: 'status',
      header: '',
      className: 'text-right',
      render: (b) =>
        b.status === 'open' ? (
          <span className="text-xs font-medium text-accent">Review</span>
        ) : (
          <span className="text-xs capitalize text-ink-faint">{b.status}</span>
        ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      rows={breaks}
      rowKey={(b) => b.breakId}
      onRowClick={(b) => onSelect(b.breakId)}
      selectable
      selectedKeys={selectedKeys}
      onToggleSelect={onToggleSelect}
      emptyMessage="No breaks in this run."
    />
  );
}
