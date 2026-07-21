interface BulkActionBarProps {
  selectedCount: number;
  onResolve: () => void;
  onMarkFalsePositive: () => void;
  onClear: () => void;
  pending?: boolean;
}

export function BulkActionBar({ selectedCount, onResolve, onMarkFalsePositive, onClear, pending }: BulkActionBarProps) {
  if (selectedCount === 0) return null;

  return (
    <div className="sticky top-0 z-10 flex items-center justify-between gap-3 rounded-md border border-accent/30 bg-accent-subtle px-3 py-2">
      <span className="text-[13px] font-medium text-ink">{selectedCount} break(s) selected</span>
      <div className="flex gap-2">
        <button
          onClick={onMarkFalsePositive}
          disabled={pending}
          className="rounded-md border border-surface-muted bg-white px-3 py-1.5 text-xs font-medium text-ink-muted hover:bg-surface-subtle disabled:opacity-40"
        >
          Mark False Positive
        </button>
        <button
          onClick={onResolve}
          disabled={pending}
          className="rounded-md bg-accent px-3 py-1.5 text-xs font-medium text-white hover:bg-accent-hover disabled:opacity-40"
        >
          Resolve Selected
        </button>
        <button onClick={onClear} className="rounded-md px-2 py-1.5 text-xs font-medium text-ink-faint hover:text-ink">
          Clear
        </button>
      </div>
    </div>
  );
}
