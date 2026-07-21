import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { BreakDetailPanel } from '@/components/reconciliation/BreakDetailPanel';
import { BreakTable } from '@/components/reconciliation/BreakTable';
import { BulkActionBar } from '@/components/reconciliation/BulkActionBar';
import { RunList } from '@/components/reconciliation/RunList';
import {
  useAllOpenBreaks,
  useBreaks,
  useBulkResolveBreaks,
  useRuns,
  useSignOffRun,
} from '@/hooks/useReconciliation';

export function Reconciliation() {
  const [searchParams, setSearchParams] = useSearchParams();
  const view = searchParams.get('view');
  const [selectedRunId, setSelectedRunId] = useState<string | null>(searchParams.get('run'));
  const [selectedBreakId, setSelectedBreakId] = useState<string | null>(null);
  const [selectedKeys, setSelectedKeys] = useState<Set<string>>(new Set());

  const { data: runs, isLoading: runsLoading } = useRuns();
  const { data: runBreaks, isLoading: runBreaksLoading } = useBreaks(view === 'breaks' ? null : selectedRunId);
  const { data: flattenedBreaks, isLoading: flattenedLoading } = useAllOpenBreaks(view === 'breaks' ? runs : undefined);

  const bulkResolveMutation = useBulkResolveBreaks(selectedRunId ?? '');
  const signOffMutation = useSignOffRun();

  const activeRun = runs?.find((r) => r.runId === selectedRunId);
  const breaks = useMemo(
    () => (view === 'breaks' ? flattenedBreaks ?? [] : runBreaks ?? []),
    [view, flattenedBreaks, runBreaks]
  );

  const panelRunId = useMemo(() => {
    if (view === 'breaks') return breaks.find((b) => b.breakId === selectedBreakId)?.runId ?? '';
    return selectedRunId ?? '';
  }, [view, breaks, selectedBreakId, selectedRunId]);

  function toggleSelect(breakId: string) {
    setSelectedKeys((prev) => {
      const next = new Set(prev);
      if (next.has(breakId)) next.delete(breakId);
      else next.add(breakId);
      return next;
    });
  }

  function backToOverview() {
    setSelectedRunId(null);
    setSelectedKeys(new Set());
    const params = new URLSearchParams(searchParams);
    params.delete('view');
    params.delete('run');
    setSearchParams(params, { replace: true });
  }

  function selectRun(runId: string) {
    setSelectedRunId(runId);
    setSelectedKeys(new Set());
  }

  if (view === 'breaks') {
    return (
      <div className="mx-auto max-w-5xl px-8 py-6">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold text-ink">Today&apos;s Breaks</h1>
          <button onClick={backToOverview} className="text-xs font-medium text-ink-muted hover:text-ink">
            &larr; Back to overview
          </button>
        </div>
        <div className="mt-4 flex flex-col gap-3 rounded-lg border border-surface-muted bg-white p-4">
          <BulkActionBar
            selectedCount={selectedKeys.size}
            pending={bulkResolveMutation.isPending}
            onClear={() => setSelectedKeys(new Set())}
            onResolve={() =>
              bulkResolveMutation.mutate(
                { breakIds: Array.from(selectedKeys), resolutionType: 'resolved_with_note', note: 'Bulk resolved.' },
                { onSuccess: () => setSelectedKeys(new Set()) }
              )
            }
            onMarkFalsePositive={() =>
              bulkResolveMutation.mutate(
                { breakIds: Array.from(selectedKeys), resolutionType: 'false_positive', note: 'Bulk marked as false positive.' },
                { onSuccess: () => setSelectedKeys(new Set()) }
              )
            }
          />
          {flattenedLoading ? (
            <p className="py-6 text-center text-sm text-ink-faint">Loading breaks…</p>
          ) : (
            <BreakTable
              breaks={breaks}
              onSelect={setSelectedBreakId}
              selectedKeys={selectedKeys}
              onToggleSelect={toggleSelect}
            />
          )}
        </div>
        <BreakDetailPanel breakId={selectedBreakId} runId={panelRunId} onClose={() => setSelectedBreakId(null)} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-8 py-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-ink">Reconciliation</h1>
        {selectedRunId && (
          <button onClick={backToOverview} className="text-xs font-medium text-ink-muted hover:text-ink">
            &larr; Back to overview
          </button>
        )}
      </div>

      {!selectedRunId ? (
        <div className="mt-4 rounded-lg border border-surface-muted bg-white p-4">
          {runsLoading ? (
            <p className="py-6 text-center text-sm text-ink-faint">Loading runs…</p>
          ) : (
            <RunList runs={runs ?? []} onSelect={selectRun} />
          )}
        </div>
      ) : (
        <div className="mt-4 flex flex-col gap-3">
          {activeRun && (
            <div className="flex items-center justify-between rounded-lg border border-surface-muted bg-white px-4 py-3">
              <div>
                <div className="text-sm font-semibold text-ink">{activeRun.reconSetName}</div>
                <div className="text-xs text-ink-faint">
                  {activeRun.jurisdiction} · {activeRun.openBreakCount} open of {activeRun.breakCount} breaks ·{' '}
                  {activeRun.matchRate.toFixed(2)}% match rate
                </div>
              </div>
              {activeRun.openBreakCount === 0 && activeRun.status !== 'signed_off' && (
                <button
                  onClick={() => signOffMutation.mutate(activeRun.runId)}
                  disabled={signOffMutation.isPending}
                  className="rounded-md bg-status-good px-3 py-1.5 text-[13px] font-medium text-white hover:opacity-90 disabled:opacity-40"
                >
                  Sign Off
                </button>
              )}
              {activeRun.status === 'signed_off' && (
                <span className="text-xs font-medium text-status-good">Signed off by {activeRun.reviewedBy}</span>
              )}
            </div>
          )}

          <div className="flex flex-col gap-3 rounded-lg border border-surface-muted bg-white p-4">
            <BulkActionBar
              selectedCount={selectedKeys.size}
              pending={bulkResolveMutation.isPending}
              onClear={() => setSelectedKeys(new Set())}
              onResolve={() =>
                bulkResolveMutation.mutate(
                  { breakIds: Array.from(selectedKeys), resolutionType: 'resolved_with_note', note: 'Bulk resolved.' },
                  { onSuccess: () => setSelectedKeys(new Set()) }
                )
              }
              onMarkFalsePositive={() =>
                bulkResolveMutation.mutate(
                  { breakIds: Array.from(selectedKeys), resolutionType: 'false_positive', note: 'Bulk marked as false positive.' },
                  { onSuccess: () => setSelectedKeys(new Set()) }
                )
              }
            />
            {runBreaksLoading ? (
              <p className="py-6 text-center text-sm text-ink-faint">Loading breaks…</p>
            ) : (
              <BreakTable
                breaks={breaks}
                onSelect={setSelectedBreakId}
                selectedKeys={selectedKeys}
                onToggleSelect={toggleSelect}
              />
            )}
          </div>
        </div>
      )}

      <BreakDetailPanel breakId={selectedBreakId} runId={panelRunId} onClose={() => setSelectedBreakId(null)} />
    </div>
  );
}
