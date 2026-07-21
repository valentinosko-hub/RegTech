// Central polling configuration, per ARCHITECTURE.md. Keeping intervals
// here (rather than scattered as magic numbers in each hook) means Phase
// 2/3 can tune them in one place once real query latency is known.
export const POLL_INTERVALS = {
  reportSubmissions: 30_000,
  feedStatus: 60_000,
  activeAlerts: 30_000,
  cases: 60_000,
  savedViewCounts: 60_000,
  notifications: 60_000,
} as const;

// Reconciliation data doesn't change intraday — fetch once on mount.
export const NO_POLL = false;
