import { useNavigate } from 'react-router-dom';

import { DataTable, type DataTableColumn } from '@/components/shared/DataTable';
import { CaseStatusPill, SeverityDot } from '@/components/shared/StatusBadge';
import { formatAge } from '@/lib/format';
import type { Case } from '@/types';

interface CaseListProps {
  cases: Case[];
  emptyMessage?: string;
}

export function CaseList({ cases, emptyMessage }: CaseListProps) {
  const navigate = useNavigate();

  const columns: DataTableColumn<Case>[] = [
    {
      key: 'severity',
      header: '',
      className: 'w-6',
      render: (c) => <SeverityDot severity={c.severity} />,
    },
    {
      key: 'caseId',
      header: 'Case ID',
      render: (c) => <span className="font-mono text-xs font-medium text-ink">{c.caseId}</span>,
    },
    {
      key: 'title',
      header: 'Title',
      className: 'max-w-md',
      render: (c) => <span className="line-clamp-1">{c.title}</span>,
    },
    { key: 'status', header: 'Status', render: (c) => <CaseStatusPill status={c.status} /> },
    { key: 'jurisdiction', header: 'Jurisdiction', render: (c) => c.jurisdiction ?? '—' },
    { key: 'vendor', header: 'Vendor', render: (c) => c.vendor ?? '—' },
    { key: 'owner', header: 'Owner', render: (c) => c.owner },
    {
      key: 'age',
      header: 'Age',
      className: 'text-right',
      render: (c) => <span className="text-ink-muted">{formatAge(c.createdAt)}</span>,
    },
  ];

  return (
    <DataTable
      columns={columns}
      rows={cases}
      rowKey={(c) => c.caseId}
      onRowClick={(c) => navigate(`/cases/${c.caseId}`)}
      emptyMessage={emptyMessage ?? 'No cases match this view.'}
    />
  );
}
