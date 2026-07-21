import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { BellIcon } from '@/components/shared/icons';
import { formatRelative } from '@/lib/format';
import { useMarkAllNotificationsRead, useMarkNotificationRead, useNotifications } from '@/hooks/useShell';
import type { Notification, NotificationType } from '@/types';

const TYPE_LABELS: Record<NotificationType, string> = {
  alert_fired: 'Alert',
  case_assigned: 'Case',
  report_submitted: 'Report',
  recon_completed: 'Reconciliation',
};

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { data: notifications } = useNotifications();
  const markRead = useMarkNotificationRead();
  const markAllRead = useMarkAllNotificationsRead();

  const unreadCount = notifications?.filter((n) => !n.read).length ?? 0;

  useEffect(() => {
    if (!open) return;
    function onClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, [open]);

  function handleClick(notification: Notification) {
    if (!notification.read) markRead.mutate(notification.id);
    setOpen(false);
    if (notification.link) navigate(notification.link);
  }

  return (
    <div className="relative" ref={containerRef}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label="Notifications"
        className="relative flex h-8 w-8 items-center justify-center rounded-md text-ink-muted transition hover:bg-surface-subtle hover:text-ink"
      >
        <BellIcon className="h-[18px] w-[18px]" />
        {unreadCount > 0 && (
          <span className="absolute right-0.5 top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-status-bad px-1 text-[10px] font-semibold text-white">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-10 z-50 w-96 rounded-lg border border-surface-muted bg-white shadow-panel">
          <div className="flex items-center justify-between border-b border-surface-muted px-4 py-2.5">
            <span className="text-sm font-semibold text-ink">Notifications</span>
            {unreadCount > 0 && (
              <button
                onClick={() => markAllRead.mutate()}
                className="text-xs font-medium text-accent hover:text-accent-hover"
              >
                Mark all read
              </button>
            )}
          </div>
          <div className="max-h-96 overflow-y-auto">
            {!notifications || notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-sm text-ink-faint">No notifications.</div>
            ) : (
              notifications.map((notification) => (
                <button
                  key={notification.id}
                  onClick={() => handleClick(notification)}
                  className={`flex w-full flex-col gap-0.5 border-b border-surface-muted/70 px-4 py-2.5 text-left transition last:border-0 hover:bg-surface-subtle ${
                    notification.read ? '' : 'bg-accent-subtle/40'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[11px] font-semibold uppercase tracking-wide text-ink-faint">
                      {TYPE_LABELS[notification.type]}
                    </span>
                    <span className="shrink-0 text-[11px] text-ink-faint">{formatRelative(notification.createdAt)}</span>
                  </div>
                  <div className="text-[13px] font-medium text-ink">{notification.title}</div>
                  {notification.body && <div className="text-xs text-ink-muted">{notification.body}</div>}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
