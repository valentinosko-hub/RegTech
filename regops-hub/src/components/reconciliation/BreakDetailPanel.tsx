import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { CategoryBadge } from '@/components/shared/StatusBadge';
import { SlidePanel } from '@/components/shared/SlidePanel';
import { useBreakDetail, useCreateCaseFromBreak, useResolveBreak } from '@/hooks/useReconciliation';

interface BreakDetailPanelProps {
  breakId: string | null;
  runId: string;
  onClose: () => void;
}

export function BreakDetailPanel({ breakId, runId, onClose }: BreakDetailPanelProps) {
  const { data: brk } = useBreakDetail(breakId);
  const resolveMutation = useResolveBreak(runId);
  const createCaseMutation = useCreateCaseFromBreak(runId);
  const navigate = useNavigate();
  const [noteMode, setNoteMode] = useState(false);
  const [note, setNote] = useState('');

  function resolve(resolutionType: 'mapping_applied' | 'resolved_with_note' | 'false_positive', extraNote?: string) {
    if (!brk) return;
    resolveMutation.mutate(
      {
        breakId: brk.breakId,
        payload: {
          resolutionType,
          note: extraNote ?? (resolutionType === 'false_positive' ? 'Marked as false positive.' : undefined),
          mappingRuleId: resolutionType === 'mapping_applied' ? (brk.linkedMappingRuleId ?? undefined) : undefined,
        },
      },
      { onSuccess: () => onClose() }
    );
  }

  const recordKeys = brk ? Array.from(new Set([...Object.keys(brk.sourceRecord), ...Object.keys(brk.targetRecord)])) : [];
  const isResolved = brk && brk.status !== 'open';

  return (
    <SlidePanel open={breakId !== null} onClose={onClose} title={brk?.breakId ?? 'Break'} subtitle={brk?.fieldName} widthClassName="w-[560px]">
      {!brk ? (
        <p className="text-sm text-ink-faint">Loading…</p>
      ) : (
        <div className="flex flex-col gap-5">
          <div className="flex items-center gap-2">
            <CategoryBadge category={brk.category} />
            {isResolved && (
              <span className="rounded bg-surface-muted px-1.5 py-0.5 text-[10px] font-semibold capitalize text-ink-muted">
                {brk.status}
              </span>
            )}
          </div>

          <section>
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-faint">Record Comparison</h3>
            <div className="overflow-hidden rounded-md border border-surface-muted">
              <div className="grid grid-cols-[100px_1fr_1fr] bg-surface-subtle px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wide text-ink-faint">
                <span>Field</span>
                <span>Source</span>
                <span>Target</span>
              </div>
              {recordKeys.map((key) => {
                const mismatch = key === brk.fieldName;
                const sourceVal = brk.sourceRecord[key] ?? '—';
                const targetVal = brk.targetRecord[key] ?? '—';
                return (
                  <div
                    key={key}
                    className={`grid grid-cols-[100px_1fr_1fr] border-t border-surface-muted px-3 py-1.5 text-xs ${
                      mismatch ? 'bg-status-warn/10' : ''
                    }`}
                  >
                    <span className="font-medium text-ink-muted">{key}</span>
                    <span className={`font-mono ${mismatch ? 'font-semibold text-status-warn' : 'text-ink'}`}>{sourceVal}</span>
                    <span className={`font-mono ${mismatch ? 'font-semibold text-status-warn' : 'text-ink'}`}>{targetVal}</span>
                  </div>
                );
              })}
            </div>
          </section>

          <section className="rounded-md bg-accent-subtle px-3 py-2.5">
            <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-accent">AI Explanation</h3>
            {brk.aiExplanation ? (
              <p className="text-sm text-ink">{brk.aiExplanation}</p>
            ) : (
              <p className="text-sm text-ink-faint">Categorising this break — explanation will appear shortly.</p>
            )}
          </section>

          {brk.linkedCaseId && (
            <button
              onClick={() => navigate(`/cases/${brk.linkedCaseId}`)}
              className="w-full rounded-md border border-surface-muted px-3 py-2 text-[13px] font-medium text-ink-muted hover:bg-surface-subtle"
            >
              View Case {brk.linkedCaseId}
            </button>
          )}

          {!isResolved && (
            <section className="flex flex-col gap-2 border-t border-surface-muted pt-4">
              <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-faint">Resolution</h3>
              {brk.linkedMappingRuleId && (
                <button
                  onClick={() => resolve('mapping_applied')}
                  disabled={resolveMutation.isPending}
                  className="rounded-md bg-accent px-3 py-2 text-[13px] font-medium text-white hover:bg-accent-hover disabled:opacity-40"
                >
                  Apply Mapping Rule
                </button>
              )}

              {noteMode ? (
                <div className="flex flex-col gap-2">
                  <textarea
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    rows={3}
                    placeholder="Resolution note…"
                    className="rounded-md border border-surface-muted px-3 py-1.5 text-sm text-ink focus:border-accent focus:outline-none"
                  />
                  <div className="flex justify-end gap-2">
                    <button onClick={() => setNoteMode(false)} className="px-2 py-1 text-xs font-medium text-ink-faint">
                      Cancel
                    </button>
                    <button
                      onClick={() => resolve('resolved_with_note', note.trim() || 'Resolved with note.')}
                      disabled={!note.trim() || resolveMutation.isPending}
                      className="rounded-md bg-accent px-3 py-1.5 text-xs font-medium text-white hover:bg-accent-hover disabled:opacity-40"
                    >
                      Confirm
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setNoteMode(true)}
                  className="rounded-md border border-surface-muted px-3 py-2 text-[13px] font-medium text-ink-muted hover:bg-surface-subtle"
                >
                  Resolve with Note
                </button>
              )}

              <button
                onClick={() => resolve('false_positive')}
                disabled={resolveMutation.isPending}
                className="rounded-md border border-surface-muted px-3 py-2 text-[13px] font-medium text-ink-muted hover:bg-surface-subtle disabled:opacity-40"
              >
                Mark False Positive
              </button>
              <button
                onClick={() =>
                  createCaseMutation.mutate(brk.breakId, {
                    onSuccess: (created) => navigate(`/cases/${created.caseId}`),
                  })
                }
                disabled={createCaseMutation.isPending}
                className="rounded-md border border-surface-muted px-3 py-2 text-[13px] font-medium text-ink-muted hover:bg-surface-subtle disabled:opacity-40"
              >
                Create Case
              </button>
            </section>
          )}
        </div>
      )}
    </SlidePanel>
  );
}
