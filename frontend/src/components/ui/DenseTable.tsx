import React, { useState, useMemo } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Search,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Inbox,
} from 'lucide-react';

export interface ColumnDef<T> {
  key: string;
  header: string;
  render?: (row: T, index: number) => React.ReactNode;
  align?: 'left' | 'center' | 'right';
  sortable?: boolean;
  isNumeric?: boolean;
  width?: string;
}

export interface DenseTableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  keyField?: keyof T | ((row: T) => string | number);
  onRowClick?: (row: T) => void;
  searchable?: boolean;
  searchPlaceholder?: string;
  searchFilter?: (row: T, query: string) => boolean;
  pageSize?: number;
  emptyTitle?: string;
  emptyDescription?: string;
  className?: string;
  headerSlot?: React.ReactNode;
}

export function DenseTable<T extends Record<string, any>>({
  columns,
  data,
  keyField = 'id',
  onRowClick,
  searchable = true,
  searchPlaceholder = 'Search records...',
  searchFilter,
  pageSize = 10,
  emptyTitle = 'No matching records',
  emptyDescription = 'Try adjusting your search filters or resetting search parameters.',
  className = '',
  headerSlot,
}: DenseTableProps<T>) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [currentPage, setCurrentPage] = useState(0);

  // Filter
  const filteredData = useMemo(() => {
    if (!searchQuery.trim()) return data;
    const query = searchQuery.toLowerCase();

    if (searchFilter) {
      return data.filter((row) => searchFilter(row, query));
    }

    return data.filter((row) =>
      Object.values(row).some((val) => {
        if (val === null || val === undefined) return false;
        return String(val).toLowerCase().includes(query);
      })
    );
  }, [data, searchQuery, searchFilter]);

  // Sort
  const sortedData = useMemo(() => {
    if (!sortKey) return filteredData;

    return [...filteredData].sort((a, b) => {
      const valA = a[sortKey];
      const valB = b[sortKey];

      if (valA === valB) return 0;
      if (valA === null || valA === undefined) return 1;
      if (valB === null || valB === undefined) return -1;

      let comparison = 0;
      if (typeof valA === 'number' && typeof valB === 'number') {
        comparison = valA - valB;
      } else {
        comparison = String(valA).localeCompare(String(valB));
      }

      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [filteredData, sortKey, sortDirection]);

  // Pagination
  const totalPages = Math.ceil(sortedData.length / pageSize) || 1;
  const paginatedData = useMemo(() => {
    const start = currentPage * pageSize;
    return sortedData.slice(start, start + pageSize);
  }, [sortedData, currentPage, pageSize]);

  const handleSort = (key: string, sortable?: boolean) => {
    if (!sortable) return;
    if (sortKey === key) {
      if (sortDirection === 'asc') {
        setSortDirection('desc');
      } else {
        setSortKey(null);
        setSortDirection('asc');
      }
    } else {
      setSortKey(key);
      setSortDirection('asc');
    }
  };

  const getRowKey = (row: T, index: number): string | number => {
    if (typeof keyField === 'function') {
      return keyField(row);
    }
    return row[keyField] ?? index;
  };

  return (
    <div
      className={`bg-white dark:bg-[#15171C] border border-neutral-200 dark:border-neutral-800 rounded-2xl overflow-hidden shadow-xs space-y-0 ${className}`}
    >
      {/* Table Toolbar */}
      {(searchable || headerSlot) && (
        <div className="p-3 sm:p-4 border-b border-neutral-100 dark:border-neutral-800/80 flex flex-col sm:flex-row items-center justify-between gap-3 bg-neutral-50/50 dark:bg-neutral-900/30">
          {searchable ? (
            <div className="relative w-full sm:w-72">
              <Search className="w-3.5 h-3.5 text-neutral-400 absolute left-3 top-2.5 pointer-events-none" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setCurrentPage(0);
                }}
                placeholder={searchPlaceholder}
                className="w-full pl-8.5 pr-3 py-1.5 text-xs bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700/80 rounded-lg text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:outline-none focus:border-[#6B4226] dark:focus:border-[#8C5E3C] focus:ring-1 focus:ring-[#6B4226]/30 transition-all font-medium"
              />
            </div>
          ) : (
            <div />
          )}

          {headerSlot && <div className="w-full sm:w-auto shrink-0">{headerSlot}</div>}
        </div>
      )}

      {/* Table Body */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-neutral-50/80 dark:bg-[#101216] border-b border-neutral-200 dark:border-neutral-800">
              {columns.map((col) => {
                const isSorted = sortKey === col.key;
                const alignClass =
                  col.align === 'right' || col.isNumeric
                    ? 'text-right'
                    : col.align === 'center'
                    ? 'text-center'
                    : 'text-left';

                return (
                  <th
                    key={col.key}
                    style={{ width: col.width }}
                    onClick={() => handleSort(col.key, col.sortable)}
                    className={`py-2.5 px-3.5 font-semibold text-[11px] uppercase tracking-wider text-neutral-500 dark:text-neutral-400 select-none ${alignClass} ${
                      col.sortable ? 'cursor-pointer hover:text-neutral-900 dark:hover:text-neutral-200' : ''
                    }`}
                  >
                    <div
                      className={`inline-flex items-center gap-1.5 ${
                        col.align === 'right' || col.isNumeric ? 'justify-end' : ''
                      }`}
                    >
                      <span>{col.header}</span>
                      {col.sortable && (
                        <span className="text-neutral-400">
                          {isSorted ? (
                            sortDirection === 'asc' ? (
                              <ArrowUp className="w-3 h-3 text-[#6B4226] dark:text-[#8C5E3C]" />
                            ) : (
                              <ArrowDown className="w-3 h-3 text-[#6B4226] dark:text-[#8C5E3C]" />
                            )
                          ) : (
                            <ArrowUpDown className="w-3 h-3 opacity-40 hover:opacity-100" />
                          )}
                        </span>
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800/60">
            {paginatedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="py-12 px-4 text-center">
                  <div className="max-w-xs mx-auto space-y-1.5">
                    <Inbox className="w-6 h-6 text-neutral-400 mx-auto" />
                    <p className="text-xs font-semibold text-neutral-800 dark:text-neutral-200">
                      {emptyTitle}
                    </p>
                    <p className="text-[11px] text-neutral-500">{emptyDescription}</p>
                  </div>
                </td>
              </tr>
            ) : (
              paginatedData.map((row, idx) => (
                <tr
                  key={getRowKey(row, idx)}
                  onClick={() => onRowClick?.(row)}
                  className={`transition-colors ${
                    onRowClick
                      ? 'hover:bg-neutral-50 dark:hover:bg-neutral-900/50 cursor-pointer group'
                      : ''
                  }`}
                >
                  {columns.map((col) => {
                    const alignClass =
                      col.align === 'right' || col.isNumeric
                        ? 'text-right font-mono'
                        : col.align === 'center'
                        ? 'text-center'
                        : 'text-left';

                    return (
                      <td
                        key={col.key}
                        className={`py-2 px-3.5 text-neutral-800 dark:text-neutral-200 ${alignClass}`}
                      >
                        {col.render ? col.render(row, idx) : row[col.key] ?? '—'}
                      </td>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {totalPages > 1 && (
        <div className="p-3 border-t border-neutral-100 dark:border-neutral-800/80 flex items-center justify-between text-xs text-neutral-500 dark:text-neutral-400 bg-neutral-50/30 dark:bg-neutral-900/20">
          <div>
            Showing <strong className="text-neutral-800 dark:text-neutral-200">{currentPage * pageSize + 1}</strong> to{' '}
            <strong className="text-neutral-800 dark:text-neutral-200">
              {Math.min((currentPage + 1) * pageSize, sortedData.length)}
            </strong>{' '}
            of <strong className="text-neutral-800 dark:text-neutral-200">{sortedData.length}</strong> entries
          </div>

          <div className="flex items-center space-x-1.5">
            <button
              onClick={() => setCurrentPage((p) => Math.max(p - 1, 0))}
              disabled={currentPage === 0}
              className="p-1.5 rounded-lg border border-neutral-200 dark:border-neutral-700 hover:bg-neutral-100 dark:hover:bg-neutral-800 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <span className="px-2 text-xs font-mono font-medium">
              {currentPage + 1} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages - 1))}
              disabled={currentPage >= totalPages - 1}
              className="p-1.5 rounded-lg border border-neutral-200 dark:border-neutral-700 hover:bg-neutral-100 dark:hover:bg-neutral-800 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
