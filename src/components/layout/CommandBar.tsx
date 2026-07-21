import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { SearchIcon } from '@/components/shared/icons';
import { useSearch } from '@/hooks/useShell';

const CASE_ID_PATTERN = /^INC-\d+$/i;
const PASTE_LENGTH_THRESHOLD = 40;

interface CommandBarProps {
  onPasteDetected: (text: string) => void;
}

export function CommandBar({ onPasteDetected }: CommandBarProps) {
  const [value, setValue] = useState('');
  const [focused, setFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const { data: results } = useSearch(value);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
        inputRef.current?.select();
      }
      if (e.key === 'Escape' && document.activeElement === inputRef.current) {
        inputRef.current?.blur();
      }
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  function handlePaste(e: React.ClipboardEvent<HTMLInputElement>) {
    const text = e.clipboardData.getData('text');
    if (text.trim().length >= PASTE_LENGTH_THRESHOLD) {
      e.preventDefault();
      onPasteDetected(text);
      setValue('');
      inputRef.current?.blur();
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed) return;
    if (CASE_ID_PATTERN.test(trimmed)) {
      navigate(`/cases/${trimmed.toUpperCase()}`);
      setValue('');
      inputRef.current?.blur();
      return;
    }
    if (results && results.length > 0) {
      navigate(results[0].href);
      setValue('');
      inputRef.current?.blur();
    }
  }

  const showDropdown = focused && value.trim().length > 0 && results && results.length > 0;

  return (
    <div className="relative w-full max-w-xl">
      <form onSubmit={handleSubmit}>
        <div className="flex items-center gap-2 rounded-md border border-surface-muted bg-surface-subtle px-3 py-1.5 focus-within:border-accent focus-within:bg-white focus-within:ring-1 focus-within:ring-accent/30">
          <SearchIcon className="h-4 w-4 shrink-0 text-ink-faint" />
          <input
            ref={inputRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onPaste={handlePaste}
            onFocus={() => setFocused(true)}
            onBlur={() => setTimeout(() => setFocused(false), 120)}
            placeholder="Search cases, paste an alert, or jump to INC-2851…"
            className="w-full bg-transparent text-[13px] text-ink placeholder:text-ink-faint focus:outline-none"
          />
          <kbd className="hidden shrink-0 rounded border border-surface-muted bg-white px-1.5 py-0.5 text-[10px] font-medium text-ink-faint sm:block">
            ⌘K
          </kbd>
        </div>
      </form>

      {showDropdown && (
        <div className="absolute left-0 top-full z-50 mt-1.5 w-full rounded-md border border-surface-muted bg-white shadow-panel">
          {results.map((result) => (
            <button
              key={`${result.type}-${result.id}`}
              onMouseDown={(e) => {
                e.preventDefault();
                navigate(result.href);
                setValue('');
              }}
              className="flex w-full flex-col gap-0.5 border-b border-surface-muted/70 px-3 py-2 text-left last:border-0 hover:bg-surface-subtle"
            >
              <span className="text-[13px] font-medium text-ink">{result.label}</span>
              <span className="text-[11px] text-ink-faint">{result.sublabel}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
