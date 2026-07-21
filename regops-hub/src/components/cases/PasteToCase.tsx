import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useCreateCase, useExtractCase } from '@/hooks/useCases';
import type { CaseType, FieldConfidence, Jurisdiction, Severity, Vendor } from '@/types';

const JURISDICTIONS: Jurisdiction[] = ['ASIC', 'MiFID', 'EMIR', 'FCA', 'MAS'];
const VENDORS: Vendor[] = ['Cappitech', 'Kaizen', 'UnaVista', 'DTCC'];
const SEVERITIES: Severity[] = ['P1', 'P2', 'P3', 'P4'];
const CASE_TYPES: CaseType[] = ['incident', 'task', 'query'];

interface PasteToCaseProps {
  initialText: string;
  onClose: () => void;
}

type Stage = 'paste' | 'extracting' | 'preview' | 'manual';

function confidenceClass(confidence: FieldConfidence): string {
  if (confidence === 'suggested') return 'border-dashed border-accent bg-accent-subtle/30';
  return 'border-surface-muted';
}

export function PasteToCase({ initialText, onClose }: PasteToCaseProps) {
  const [stage, setStage] = useState<Stage>(initialText ? 'extracting' : 'paste');
  const [pasteText, setPasteText] = useState(initialText);
  const [duplicateWarning, setDuplicateWarning] = useState<{ caseId: string; title: string } | null>(null);

  const [title, setTitle] = useState('');
  const [titleConfidence, setTitleConfidence] = useState<FieldConfidence>('unknown');
  const [severity, setSeverity] = useState<Severity>('P3');
  const [jurisdiction, setJurisdiction] = useState<Jurisdiction | ''>('');
  const [vendor, setVendor] = useState<Vendor | ''>('');
  const [caseType, setCaseType] = useState<CaseType>('incident');
  const [description, setDescription] = useState('');
  const [descriptionConfidence, setDescriptionConfidence] = useState<FieldConfidence>('unknown');

  const extractMutation = useExtractCase();
  const createMutation = useCreateCase();
  const navigate = useNavigate();

  useEffect(() => {
    if (stage !== 'extracting') return;
    extractMutation.mutate(pasteText, {
      onSuccess: (extraction) => {
        if (extraction.status === 'failed') {
          setStage('manual');
          return;
        }
        setTitle(extraction.title.value ?? '');
        setTitleConfidence(extraction.title.confidence);
        setDescription(extraction.description.value ?? pasteText);
        setDescriptionConfidence(extraction.description.confidence);
        if (extraction.severity.value) setSeverity(extraction.severity.value as Severity);
        if (extraction.jurisdiction.value) setJurisdiction(extraction.jurisdiction.value as Jurisdiction);
        if (extraction.vendor.value) setVendor(extraction.vendor.value as Vendor);
        if (extraction.caseType.value) setCaseType(extraction.caseType.value as CaseType);
        setDuplicateWarning(extraction.duplicateWarning);
        setStage('preview');
      },
      onError: () => setStage('manual'),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage]);

  function handlePasteAreaChange(text: string) {
    setPasteText(text);
  }

  function handleExtractClick() {
    if (!pasteText.trim()) return;
    setStage('extracting');
  }

  function handleSubmit() {
    if (!title.trim()) return;
    createMutation.mutate(
      {
        title: title.trim(),
        description: description.trim() || null,
        severity,
        jurisdiction: jurisdiction || null,
        vendor: vendor || null,
        caseType,
        sourceType: 'paste',
      },
      {
        onSuccess: (created) => {
          onClose();
          navigate(`/cases/${created.caseId}`);
        },
      }
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/30 p-4">
      <div className="flex max-h-[85vh] w-full max-w-lg flex-col rounded-lg bg-white shadow-panel">
        <div className="flex items-center justify-between border-b border-surface-muted px-5 py-4">
          <h2 className="text-sm font-semibold text-ink">New Case</h2>
          <button onClick={onClose} className="rounded-md p-1 text-ink-faint hover:bg-surface-subtle hover:text-ink">
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {stage === 'paste' && (
            <div className="flex flex-col gap-3">
              <p className="text-xs text-ink-muted">
                Paste an alert, email thread, or chat message. We&apos;ll extract the case details automatically.
              </p>
              <textarea
                autoFocus
                value={pasteText}
                onChange={(e) => handlePasteAreaChange(e.target.value)}
                rows={10}
                placeholder="Paste operational text here…"
                className="w-full rounded-md border border-surface-muted px-3 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent/30"
              />
              <div className="flex items-center justify-between">
                <button onClick={() => setStage('manual')} className="text-xs font-medium text-ink-muted hover:text-ink">
                  Enter details manually instead
                </button>
                <button
                  onClick={handleExtractClick}
                  disabled={!pasteText.trim()}
                  className="rounded-md bg-accent px-3 py-1.5 text-[13px] font-medium text-white transition hover:bg-accent-hover disabled:opacity-40"
                >
                  Extract details
                </button>
              </div>
            </div>
          )}

          {stage === 'extracting' && (
            <div className="flex flex-col items-center gap-3 py-14">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
              <p className="text-sm text-ink-muted">Extracting case details…</p>
            </div>
          )}

          {(stage === 'preview' || stage === 'manual') && (
            <div className="flex flex-col gap-4">
              {stage === 'manual' && (
                <p className="rounded-md bg-status-warn/10 px-3 py-2 text-xs text-status-warn">
                  Automatic extraction wasn&apos;t available — enter the case details below.
                </p>
              )}
              {duplicateWarning && (
                <p className="rounded-md bg-status-warn/10 px-3 py-2 text-xs text-ink">
                  Possible duplicate: a similar open case already exists —{' '}
                  <span className="font-semibold">
                    {duplicateWarning.caseId}: {duplicateWarning.title}
                  </span>
                  .
                </p>
              )}

              <Field label="Title" required>
                <input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Short summary of the issue"
                  className={`w-full rounded-md border px-3 py-1.5 text-sm text-ink focus:outline-none ${confidenceClass(titleConfidence)}`}
                />
              </Field>

              <div className="grid grid-cols-2 gap-3">
                <Field label="Severity" required>
                  <select
                    value={severity}
                    onChange={(e) => setSeverity(e.target.value as Severity)}
                    className="w-full rounded-md border border-surface-muted px-3 py-1.5 text-sm text-ink focus:border-accent focus:outline-none"
                  >
                    {SEVERITIES.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Case Type">
                  <select
                    value={caseType}
                    onChange={(e) => setCaseType(e.target.value as CaseType)}
                    className="w-full rounded-md border border-surface-muted px-3 py-1.5 text-sm capitalize text-ink focus:border-accent focus:outline-none"
                  >
                    {CASE_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <Field label="Jurisdiction">
                  <select
                    value={jurisdiction}
                    onChange={(e) => setJurisdiction(e.target.value as Jurisdiction | '')}
                    className="w-full rounded-md border border-surface-muted px-3 py-1.5 text-sm text-ink focus:border-accent focus:outline-none"
                  >
                    <option value="">—</option>
                    {JURISDICTIONS.map((j) => (
                      <option key={j} value={j}>
                        {j}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Vendor">
                  <select
                    value={vendor}
                    onChange={(e) => setVendor(e.target.value as Vendor | '')}
                    className="w-full rounded-md border border-surface-muted px-3 py-1.5 text-sm text-ink focus:border-accent focus:outline-none"
                  >
                    <option value="">—</option>
                    {VENDORS.map((v) => (
                      <option key={v} value={v}>
                        {v}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>

              <Field label="Description">
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={4}
                  className={`w-full rounded-md border px-3 py-1.5 text-sm text-ink focus:outline-none ${confidenceClass(descriptionConfidence)}`}
                />
              </Field>
            </div>
          )}
        </div>

        {(stage === 'preview' || stage === 'manual') && (
          <div className="flex items-center justify-end gap-2 border-t border-surface-muted px-5 py-3">
            <button onClick={onClose} className="rounded-md px-3 py-1.5 text-[13px] font-medium text-ink-muted hover:bg-surface-subtle">
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={!title.trim() || createMutation.isPending}
              className="rounded-md bg-accent px-4 py-1.5 text-[13px] font-medium text-white transition hover:bg-accent-hover disabled:opacity-40"
            >
              {createMutation.isPending ? 'Creating…' : 'Create Case'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-[11px] font-medium text-ink-muted">
        {label}
        {required && <span className="text-status-bad"> *</span>}
      </span>
      {children}
    </label>
  );
}
