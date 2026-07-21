import type { ReactNode } from 'react';

interface SlidePanelProps {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: ReactNode;
  widthClassName?: string;
}

export function SlidePanel({ open, onClose, title, subtitle, children, widthClassName = 'w-[480px]' }: SlidePanelProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      <button
        aria-label="Close panel"
        className="absolute inset-0 bg-ink/25 backdrop-blur-[1px]"
        onClick={onClose}
      />
      <div className={`relative z-50 flex h-full flex-col bg-white shadow-panel ${widthClassName}`}>
        <div className="flex items-start justify-between border-b border-surface-muted px-5 py-4">
          <div className="min-w-0 pr-4">
            <h2 className="truncate text-sm font-semibold text-ink">{title}</h2>
            {subtitle && <p className="mt-0.5 truncate text-xs text-ink-muted">{subtitle}</p>}
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="shrink-0 rounded-md p-1.5 text-ink-faint transition hover:bg-surface-subtle hover:text-ink"
          >
            <CloseIcon />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-5 py-4">{children}</div>
      </div>
    </div>
  );
}

function CloseIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M4 4L12 12M12 4L4 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}
