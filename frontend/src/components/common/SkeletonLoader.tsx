import React from 'react';

export const AttentionBarSkeleton: React.FC = () => (
  <div className="w-full p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-surface dark:bg-surface-dark flex items-center justify-between animate-pulse">
    <div className="flex items-center space-x-3">
      <div className="w-5 h-5 rounded-full bg-neutral-200 dark:bg-neutral-800" />
      <div className="h-4 w-48 bg-neutral-200 dark:bg-neutral-800 rounded" />
    </div>
    <div className="flex items-center space-x-2">
      <div className="h-7 w-28 bg-neutral-200 dark:bg-neutral-800 rounded-full" />
      <div className="h-7 w-28 bg-neutral-200 dark:bg-neutral-800 rounded-full" />
    </div>
  </div>
);

export const KpiCardSkeleton: React.FC = () => (
  <div className="glass-card p-5 sm:p-6 space-y-4 animate-pulse">
    <div className="flex items-start justify-between">
      <div className="space-y-2">
        <div className="h-3 w-16 bg-neutral-200 dark:bg-neutral-800 rounded" />
        <div className="h-5 w-32 bg-neutral-200 dark:bg-neutral-800 rounded" />
      </div>
      <div className="h-5 w-16 bg-neutral-200 dark:bg-neutral-800 rounded-full" />
    </div>
    <div className="flex items-baseline justify-between pt-1">
      <div className="space-y-2">
        <div className="h-8 w-28 bg-neutral-200 dark:bg-neutral-800 rounded" />
        <div className="h-4 w-20 bg-neutral-200 dark:bg-neutral-800 rounded" />
      </div>
      <div className="w-24 h-10 bg-neutral-200 dark:bg-neutral-800 rounded" />
    </div>
    <div className="pt-3 border-t border-neutral-100 dark:border-neutral-800 flex justify-between">
      <div className="h-3 w-24 bg-neutral-200 dark:bg-neutral-800 rounded" />
      <div className="h-3 w-16 bg-neutral-200 dark:bg-neutral-800 rounded" />
    </div>
  </div>
);

export const ChartSkeleton: React.FC = () => (
  <div className="glass-panel p-6 space-y-4 animate-pulse">
    <div className="flex items-center justify-between">
      <div className="space-y-2">
        <div className="h-5 w-44 bg-neutral-200 dark:bg-neutral-800 rounded" />
        <div className="h-3 w-64 bg-neutral-200 dark:bg-neutral-800 rounded" />
      </div>
      <div className="h-8 w-32 bg-neutral-200 dark:bg-neutral-800 rounded-lg" />
    </div>
    <div className="h-72 w-full bg-neutral-100 dark:bg-neutral-900 rounded-xl flex items-end p-4 space-x-3">
      {[40, 65, 30, 85, 45, 90, 75, 60, 80, 50, 70, 95].map((h, i) => (
        <div
          key={i}
          className="flex-1 bg-neutral-200 dark:bg-neutral-800 rounded-t"
          style={{ height: `${h}%` }}
        />
      ))}
    </div>
  </div>
);

export const TableSkeleton: React.FC<{ rows?: number }> = ({ rows = 5 }) => (
  <div className="glass-panel p-5 space-y-4 animate-pulse">
    <div className="flex justify-between items-center">
      <div className="h-5 w-40 bg-neutral-200 dark:bg-neutral-800 rounded" />
      <div className="h-8 w-48 bg-neutral-200 dark:bg-neutral-800 rounded-lg" />
    </div>
    <div className="space-y-2.5">
      <div className="h-8 w-full bg-neutral-100 dark:bg-neutral-900 rounded" />
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-10 w-full bg-neutral-200/60 dark:bg-neutral-800/60 rounded" />
      ))}
    </div>
  </div>
);

export const CardListSkeleton: React.FC<{ count?: number }> = ({ count = 3 }) => (
  <div className="space-y-3">
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="glass-card p-5 space-y-3 animate-pulse">
        <div className="flex justify-between">
          <div className="h-4 w-32 bg-neutral-200 dark:bg-neutral-800 rounded" />
          <div className="h-4 w-20 bg-neutral-200 dark:bg-neutral-800 rounded-full" />
        </div>
        <div className="h-5 w-3/4 bg-neutral-200 dark:bg-neutral-800 rounded" />
        <div className="h-3 w-full bg-neutral-200 dark:bg-neutral-800 rounded" />
      </div>
    ))}
  </div>
);
