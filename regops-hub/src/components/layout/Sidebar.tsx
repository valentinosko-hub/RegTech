import { NavLink } from 'react-router-dom';

import { CasesIcon, HomeIcon, MonitorIcon, ReconIcon } from '@/components/shared/icons';
import { useCurrentUser, useSavedViewCounts } from '@/hooks/useShell';
import type { SavedViewCounts } from '@/types';

const MODULES = [
  { to: '/', label: 'Home', icon: HomeIcon },
  { to: '/monitoring', label: 'Monitoring', icon: MonitorIcon },
  { to: '/reconciliation', label: 'Reconciliation', icon: ReconIcon },
  { to: '/cases', label: 'Cases', icon: CasesIcon },
];

const SAVED_VIEWS: { key: keyof SavedViewCounts; label: string; to: string; urgent?: boolean }[] = [
  { key: 'todaysReports', label: "Today's Reports", to: '/monitoring?tab=reports' },
  { key: 'todaysReconciliation', label: "Today's Reconciliation", to: '/reconciliation' },
  { key: 'todaysBreaks', label: "Today's Breaks", to: '/reconciliation?view=breaks', urgent: true },
  { key: 'activeAlerts', label: 'Active Alerts', to: '/monitoring?tab=alerts', urgent: true },
  { key: 'myOpenCases', label: 'My Open Cases', to: '/cases?filter=mine' },
  { key: 'awaitingVendor', label: 'Awaiting Vendor Response', to: '/cases?view=awaiting_vendor' },
  { key: 'lateReports', label: 'Late Reports', to: '/monitoring?tab=reports&late=1', urgent: true },
];

export function Sidebar() {
  const { data: counts } = useSavedViewCounts();
  const { data: user } = useCurrentUser();

  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col bg-sidebar text-slate-300">
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-accent text-xs font-bold text-white">
          R
        </div>
        <div>
          <div className="text-sm font-semibold leading-tight text-white">RegOps Hub</div>
          <div className="text-[11px] leading-tight text-slate-500">RegTech Operations</div>
        </div>
      </div>

      <nav className="mt-2 flex flex-col gap-0.5 px-3">
        {MODULES.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-2.5 rounded-md px-3 py-2 text-[13px] font-medium transition ${
                isActive ? 'bg-sidebar-active text-white' : 'text-slate-300 hover:bg-sidebar-hover hover:text-white'
              }`
            }
          >
            <Icon className="h-[18px] w-[18px]" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-6 flex-1 overflow-y-auto px-3">
        <div className="px-3 pb-1.5 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
          Saved Views
        </div>
        <div className="flex flex-col gap-0.5">
          {SAVED_VIEWS.map((view) => {
            const count = counts?.[view.key] ?? 0;
            return (
              <NavLink
                key={view.key}
                to={view.to}
                className="flex items-center justify-between gap-2 rounded-md px-3 py-1.5 text-[13px] text-slate-300 transition hover:bg-sidebar-hover hover:text-white"
              >
                <span className="truncate">{view.label}</span>
                {count > 0 && (
                  <span
                    className={`shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-semibold leading-none ${
                      view.urgent ? 'bg-status-warn/20 text-status-warn' : 'bg-white/10 text-slate-300'
                    }`}
                  >
                    {count}
                  </span>
                )}
              </NavLink>
            );
          })}
        </div>
      </div>

      <div className="border-t border-sidebar-border px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-sidebar-active text-[11px] font-semibold text-white">
            {(user?.displayName ?? '?')
              .split(' ')
              .map((p) => p[0])
              .join('')
              .slice(0, 2)}
          </div>
          <div className="min-w-0">
            <div className="truncate text-[12px] font-medium text-white">{user?.displayName ?? 'Loading…'}</div>
            <div className="truncate text-[11px] capitalize text-slate-500">{user?.role ?? ''}</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
