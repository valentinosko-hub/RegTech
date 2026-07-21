import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { CaseList } from '@/components/cases/CaseList';
import { useCases } from '@/hooks/useCases';
import type { CaseFilter } from '@/services/cases';

const TABS: { key: CaseFilter; label: string }[] = [
  { key: 'mine', label: 'My Cases' },
  { key: 'open', label: 'All Open' },
  { key: 'all', label: 'All' },
];

export function Cases() {
  const [searchParams] = useSearchParams();
  const initialFilter = (searchParams.get('filter') as CaseFilter) ?? 'all';
  const view = searchParams.get('view');
  const [filter, setFilter] = useState<CaseFilter>(view === 'awaiting_vendor' ? 'all' : initialFilter);

  const { data: cases, isLoading } = useCases(filter);

  const filtered = useMemo(() => {
    if (!cases) return [];
    if (view === 'awaiting_vendor') return cases.filter((c) => c.status === 'pending_vendor');
    return cases;
  }, [cases, view]);

  return (
    <div className="mx-auto max-w-6xl px-8 py-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-ink">Cases</h1>
      </div>

      {view === 'awaiting_vendor' ? (
        <div className="mt-4 inline-flex items-center gap-2 rounded-md bg-status-warn/10 px-3 py-1.5 text-xs font-medium text-status-warn">
          Showing cases awaiting vendor response
        </div>
      ) : (
        <div className="mt-4 flex gap-1 rounded-md bg-surface-muted p-1">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setFilter(tab.key)}
              className={`rounded-md px-3 py-1.5 text-[13px] font-medium transition ${
                filter === tab.key ? 'bg-white text-ink shadow-card' : 'text-ink-muted hover:text-ink'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}

      <div className="mt-4 rounded-lg border border-surface-muted bg-white">
        {isLoading ? (
          <div className="py-10 text-center text-sm text-ink-faint">Loading cases…</div>
        ) : (
          <CaseList cases={filtered} />
        )}
      </div>
    </div>
  );
}
