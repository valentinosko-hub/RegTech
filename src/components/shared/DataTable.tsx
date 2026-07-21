import type { ReactNode } from 'react';

export interface DataTableColumn<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
  selectable?: boolean;
  selectedKeys?: Set<string>;
  onToggleSelect?: (key: string) => void;
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  onRowClick,
  emptyMessage,
  selectable,
  selectedKeys,
  onToggleSelect,
}: DataTableProps<T>) {
  if (rows.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-surface-muted bg-surface-subtle py-10 text-center text-sm text-ink-faint">
        {emptyMessage ?? 'Nothing here.'}
      </div>
    );
  }

  return (
    <table className="w-full border-collapse text-sm">
      <thead>
        <tr className="border-b border-surface-muted text-left text-[11px] font-semibold uppercase tracking-wide text-ink-faint">
          {selectable && <th className="w-9 px-3 py-2" />}
          {columns.map((col) => (
            <th key={col.key} className={`px-3 py-2 ${col.className ?? ''}`}>
              {col.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => {
          const key = rowKey(row);
          return (
            <tr
              key={key}
              onClick={() => onRowClick?.(row)}
              className={`border-b border-surface-muted/70 last:border-0 ${
                onRowClick ? 'cursor-pointer hover:bg-surface-subtle' : ''
              }`}
            >
              {selectable && (
                <td className="px-3 py-2" onClick={(e) => e.stopPropagation()}>
                  <input
                    type="checkbox"
                    className="h-3.5 w-3.5 rounded border-ink-faint/50 text-accent focus:ring-accent"
                    checked={selectedKeys?.has(key) ?? false}
                    onChange={() => onToggleSelect?.(key)}
                  />
                </td>
              )}
              {columns.map((col) => (
                <td key={col.key} className={`px-3 py-2 text-ink ${col.className ?? ''}`}>
                  {col.render(row)}
                </td>
              ))}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
