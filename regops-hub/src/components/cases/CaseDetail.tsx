import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { CaseTimeline } from '@/components/cases/CaseTimeline';
import { SeverityDot } from '@/components/shared/StatusBadge';
import { formatDateTime } from '@/lib/format';
import { useAddComment, useCaseDetail, useCloseCase, useUpdateCase } from '@/hooks/useCases';
import type { CaseStatus, Severity } from '@/types';

const STATUSES: CaseStatus[] = ['open', 'investigating', 'pending_vendor', 'closed'];
const SEVERITIES: Severity[] = ['P1', 'P2', 'P3', 'P4'];
const RESOLUTION_TYPES = [
  { value: 'resolved_with_note', label: 'Resolved' },
  { value: 'false_positive', label: 'False Positive' },
  { value: 'escalated_to_case', label: 'Escalated' },
];

export function CaseDetail() {
  const { caseId = '' } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const { data: detail, isLoading } = useCaseDetail(caseId);
  const updateMutation = useUpdateCase(caseId);
  const commentMutation = useAddComment(caseId);
  const closeMutation = useCloseCase(caseId);

  const [commentBody, setCommentBody] = useState('');
  const [showClosePanel, setShowClosePanel] = useState(false);
  const [resolutionType, setResolutionType] = useState('resolved_with_note');
  const [resolutionNote, setResolutionNote] = useState('');

  if (isLoading || !detail) {
    return <div className="p-8 text-sm text-ink-faint">Loading case…</div>;
  }

  function handleAddComment() {
    if (!commentBody.trim()) return;
    commentMutation.mutate(commentBody.trim(), { onSuccess: () => setCommentBody('') });
  }

  function handleClose() {
    if (!resolutionNote.trim()) return;
    closeMutation.mutate(
      { resolutionType, resolutionNote: resolutionNote.trim() },
      { onSuccess: () => setShowClosePanel(false) }
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-8 py-6">
      <Link to="/cases" className="text-xs font-medium text-ink-muted hover:text-ink">
        &larr; Back to cases
      </Link>

      <div className="mt-3 flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <SeverityDot severity={detail.severity} />
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-ink-faint">{detail.caseId}</span>
            </div>
            <h1 className="mt-0.5 text-lg font-semibold text-ink">{detail.title}</h1>
          </div>
        </div>
        {detail.status !== 'closed' && (
          <button
            onClick={() => setShowClosePanel((v) => !v)}
            className="shrink-0 rounded-md border border-surface-muted px-3 py-1.5 text-[13px] font-medium text-ink-muted hover:bg-surface-subtle"
          >
            Close Case
          </button>
        )}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <LabeledSelect
          label="Status"
          value={detail.status}
          options={STATUSES.map((s) => ({ value: s, label: s.replace('_', ' ') }))}
          disabled={detail.status === 'closed'}
          onChange={(v) => updateMutation.mutate({ status: v as CaseStatus })}
        />
        <LabeledSelect
          label="Severity"
          value={detail.severity}
          options={SEVERITIES.map((s) => ({ value: s, label: s }))}
          onChange={(v) => updateMutation.mutate({ severity: v as Severity })}
        />
        <span className="text-xs text-ink-faint">
          Owner: <span className="font-medium text-ink">{detail.owner}</span>
        </span>
        <span className="text-xs text-ink-faint">Opened {formatDateTime(detail.createdAt)}</span>
      </div>

      {showClosePanel && (
        <div className="mt-4 rounded-lg border border-surface-muted bg-white p-4">
          <h3 className="text-sm font-semibold text-ink">Close case</h3>
          <div className="mt-3 flex flex-col gap-3">
            <LabeledSelect
              label="Resolution type"
              value={resolutionType}
              options={RESOLUTION_TYPES}
              onChange={setResolutionType}
            />
            <label className="flex flex-col gap-1">
              <span className="text-[11px] font-medium text-ink-muted">Resolution note</span>
              <textarea
                value={resolutionNote}
                onChange={(e) => setResolutionNote(e.target.value)}
                rows={3}
                placeholder="What was found and how was it resolved?"
                className="rounded-md border border-surface-muted px-3 py-1.5 text-sm text-ink focus:border-accent focus:outline-none"
              />
            </label>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowClosePanel(false)}
                className="rounded-md px-3 py-1.5 text-[13px] font-medium text-ink-muted hover:bg-surface-subtle"
              >
                Cancel
              </button>
              <button
                onClick={handleClose}
                disabled={!resolutionNote.trim() || closeMutation.isPending}
                className="rounded-md bg-accent px-4 py-1.5 text-[13px] font-medium text-white hover:bg-accent-hover disabled:opacity-40"
              >
                Close Case
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="mt-6 grid grid-cols-3 gap-6">
        <div className="col-span-2 flex flex-col gap-6">
          {detail.description && (
            <section>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-faint">Description</h3>
              <p className="text-sm text-ink-muted">{detail.description}</p>
            </section>
          )}

          {detail.status === 'closed' && detail.resolutionNote && (
            <section className="rounded-md bg-status-good/10 px-3 py-2.5">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-status-good">Resolution</h3>
              <p className="mt-1 text-sm text-ink">{detail.resolutionNote}</p>
            </section>
          )}

          <section>
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-faint">Timeline</h3>
            <CaseTimeline events={detail.timeline} comments={detail.comments} />
          </section>

          {detail.status !== 'closed' && (
            <section className="flex flex-col gap-2">
              <textarea
                value={commentBody}
                onChange={(e) => setCommentBody(e.target.value)}
                rows={3}
                placeholder="Add a comment…"
                className="rounded-md border border-surface-muted px-3 py-2 text-sm text-ink focus:border-accent focus:outline-none"
              />
              <div className="flex justify-end">
                <button
                  onClick={handleAddComment}
                  disabled={!commentBody.trim() || commentMutation.isPending}
                  className="rounded-md bg-accent px-3 py-1.5 text-[13px] font-medium text-white hover:bg-accent-hover disabled:opacity-40"
                >
                  Comment
                </button>
              </div>
            </section>
          )}
        </div>

        <aside className="flex flex-col gap-4">
          <InfoRow label="Jurisdiction" value={detail.jurisdiction ?? '—'} />
          <InfoRow label="Vendor" value={detail.vendor ?? '—'} />
          <InfoRow label="Type" value={detail.caseType} />
          <InfoRow label="Source" value={detail.sourceType.replace('_', ' ')} />

          {detail.linkedItems.length > 0 && (
            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-faint">Linked Items</h3>
              <div className="flex flex-col gap-1.5">
                {detail.linkedItems.map((item) => (
                  <button
                    key={`${item.type}-${item.id}`}
                    onClick={() => navigate(item.href)}
                    className="rounded-md border border-surface-muted px-2.5 py-1.5 text-left text-xs text-ink-muted hover:bg-surface-subtle hover:text-ink"
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[11px] font-semibold uppercase tracking-wide text-ink-faint">{label}</div>
      <div className="mt-0.5 text-sm capitalize text-ink">{value}</div>
    </div>
  );
}

function LabeledSelect({
  label,
  value,
  options,
  onChange,
  disabled,
}: {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  return (
    <label className="flex items-center gap-1.5">
      <span className="text-[11px] font-medium text-ink-faint">{label}</span>
      <select
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-surface-muted px-2 py-1 text-xs font-medium capitalize text-ink focus:border-accent focus:outline-none disabled:bg-surface-subtle disabled:text-ink-faint"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </label>
  );
}
