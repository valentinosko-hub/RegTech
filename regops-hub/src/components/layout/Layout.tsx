import { useState } from 'react';
import { Outlet } from 'react-router-dom';

import { PasteToCase } from '@/components/cases/PasteToCase';
import { CommandBar } from '@/components/layout/CommandBar';
import { NotificationBell } from '@/components/layout/NotificationBell';
import { Sidebar } from '@/components/layout/Sidebar';

export function Layout() {
  const [pasteModalText, setPasteModalText] = useState<string | null>(null);
  const [showEmptyPasteModal, setShowEmptyPasteModal] = useState(false);

  return (
    <div className="flex h-screen bg-surface-subtle">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex items-center justify-between gap-4 border-b border-surface-muted bg-white px-6 py-3">
          <CommandBar onPasteDetected={setPasteModalText} />
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowEmptyPasteModal(true)}
              className="rounded-md bg-accent px-3 py-1.5 text-[13px] font-medium text-white transition hover:bg-accent-hover"
            >
              New Case
            </button>
            <NotificationBell />
          </div>
        </header>
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>

      {(pasteModalText !== null || showEmptyPasteModal) && (
        <PasteToCase
          initialText={pasteModalText ?? ''}
          onClose={() => {
            setPasteModalText(null);
            setShowEmptyPasteModal(false);
          }}
        />
      )}
    </div>
  );
}
