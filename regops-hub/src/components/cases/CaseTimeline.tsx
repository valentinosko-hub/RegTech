import { formatDateTime } from '@/lib/format';
import type { Comment, TimelineEvent } from '@/types';

interface TimelineItem {
  id: string;
  createdAt: string;
  kind: 'event' | 'comment';
  actor: string;
  content: string;
  eventType?: TimelineEvent['eventType'];
}

interface CaseTimelineProps {
  events: TimelineEvent[];
  comments: Comment[];
}

const EVENT_LABELS: Record<TimelineEvent['eventType'], string> = {
  created: 'Created',
  status_changed: 'Status changed',
  severity_changed: 'Severity changed',
  comment_added: 'Comment',
  escalated: 'Escalated',
  closed: 'Closed',
  linked: 'Linked',
};

export function CaseTimeline({ events, comments }: CaseTimelineProps) {
  // Comments are rendered from the `comments` list (with full body text), so
  // the corresponding "comment_added" timeline events are dropped here to
  // avoid showing the same activity twice.
  const eventItems: TimelineItem[] = events
    .filter((e) => e.eventType !== 'comment_added')
    .map((e) => ({
      id: e.id,
      createdAt: e.createdAt,
      kind: 'event',
      actor: e.actor,
      content: e.description,
      eventType: e.eventType,
    }));
  const commentItems: TimelineItem[] = comments.map((c) => ({
    id: c.id,
    createdAt: c.createdAt,
    kind: 'comment',
    actor: c.author,
    content: c.body,
  }));
  const items = [...eventItems, ...commentItems].sort(
    (a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
  );

  if (items.length === 0) {
    return <p className="text-sm text-ink-faint">No activity yet.</p>;
  }

  return (
    <ol className="flex flex-col gap-4">
      {items.map((item) => (
        <li key={item.id} className="relative flex gap-3 pl-1">
          <div className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
          <div className="min-w-0 flex-1">
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-xs font-semibold text-ink">
                {item.actor}
                {item.eventType && (
                  <span className="ml-1.5 font-normal text-ink-faint">{EVENT_LABELS[item.eventType]}</span>
                )}
              </span>
              <span className="shrink-0 text-[11px] text-ink-faint">{formatDateTime(item.createdAt)}</span>
            </div>
            <p className="mt-0.5 text-sm text-ink-muted">{item.content}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}
