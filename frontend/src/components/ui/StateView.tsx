import React from 'react';
import { AlertTriangle, RefreshCw, Sparkles, Inbox, LucideIcon } from 'lucide-react';
import { Button } from './Button';
import {
  KpiCardSkeleton,
  TableSkeleton,
  ChartSkeleton,
  CardListSkeleton,
} from '../common/SkeletonLoader';

const renderIcon = (iconInput: any, className: string = 'w-6 h-6') => {
  if (!iconInput) return null;
  if (React.isValidElement(iconInput)) {
    return iconInput;
  }
  if (
    typeof iconInput === 'function' ||
    (typeof iconInput === 'object' && iconInput !== null && '$$typeof' in iconInput)
  ) {
    const IconComp = iconInput;
    return <IconComp className={className} />;
  }
  return null;
};

export interface EmptyStateProps {
  icon?: LucideIcon | React.ReactNode;
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
  actionLoading?: boolean;
  secondaryActionText?: string;
  onSecondaryAction?: () => void;
  customAction?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon = Inbox,
  title,
  description,
  actionText,
  onAction,
  actionLoading = false,
  secondaryActionText,
  onSecondaryAction,
  customAction,
  className = '',
}) => {
  return (
    <div
      className={`bg-white dark:bg-[#15171C] border border-neutral-200 dark:border-neutral-800 rounded-2xl p-8 sm:p-12 text-center space-y-4 shadow-xs ${className}`}
    >
      <div className="mx-auto w-12 h-12 rounded-2xl bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center text-[#6B4226] dark:text-[#8C5E3C] shadow-xs">
        {renderIcon(icon, 'w-6 h-6')}
      </div>

      <div className="max-w-md mx-auto space-y-1.5">
        <h3 className="text-base sm:text-lg font-bold text-neutral-900 dark:text-neutral-100 tracking-tight">
          {title}
        </h3>
        <p className="text-xs sm:text-sm text-neutral-500 dark:text-neutral-400 font-normal leading-relaxed">
          {description}
        </p>
      </div>

      {(onAction || onSecondaryAction || customAction) && (
        <div className="flex flex-wrap items-center justify-center gap-2.5 pt-2">
          {customAction}
          {onAction && actionText && (
            <Button
              variant="primary"
              size="sm"
              isLoading={actionLoading}
              onClick={onAction}
              leftIcon={<Sparkles className="w-3.5 h-3.5" />}
            >
              {actionText}
            </Button>
          )}
          {onSecondaryAction && secondaryActionText && (
            <Button variant="secondary" size="sm" onClick={onSecondaryAction}>
              {secondaryActionText}
            </Button>
          )}
        </div>
      )}
    </div>
  );
};

export interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Unable to Load Data',
  message,
  onRetry,
  className = '',
}) => {
  return (
    <div
      className={`bg-red-50/50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/60 rounded-2xl p-6 sm:p-8 text-center space-y-3 shadow-xs ${className}`}
    >
      <div className="mx-auto w-10 h-10 rounded-xl bg-red-100 dark:bg-red-900/50 flex items-center justify-center text-red-600 dark:text-red-400">
        <AlertTriangle className="w-5 h-5" />
      </div>
      <div className="max-w-md mx-auto space-y-1">
        <h4 className="text-sm sm:text-base font-bold text-red-900 dark:text-red-200">
          {title}
        </h4>
        <p className="text-xs text-red-700 dark:text-red-300 font-normal leading-relaxed">
          {message}
        </p>
      </div>
      {onRetry && (
        <div className="pt-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
            className="border-red-300 dark:border-red-800 text-red-800 dark:text-red-200 hover:bg-red-100/50"
          >
            Retry Request
          </Button>
        </div>
      )}
    </div>
  );
};

export interface StateViewProps {
  isLoading: boolean;
  isError?: boolean;
  errorMessage?: string;
  onRetry?: () => void;
  isEmpty?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  emptyActionText?: string;
  onEmptyAction?: () => void;
  emptyActionLoading?: boolean;
  emptySecondaryActionText?: string;
  onEmptySecondaryAction?: () => void;
  emptyAction?: React.ReactNode;
  emptyIcon?: LucideIcon | React.ReactNode;
  loadingSkeleton?: 'card-grid' | 'table' | 'chart' | 'list' | 'custom';
  customSkeleton?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const StateView: React.FC<StateViewProps> = ({
  isLoading,
  isError = false,
  errorMessage = 'Failed to fetch the requested records.',
  onRetry,
  isEmpty = false,
  emptyTitle = 'No Records Found',
  emptyDescription = 'There is currently no data to display for this view.',
  emptyActionText,
  onEmptyAction,
  emptyActionLoading = false,
  emptySecondaryActionText,
  onEmptySecondaryAction,
  emptyAction,
  emptyIcon,
  loadingSkeleton = 'card-grid',
  customSkeleton,
  children,
  className = '',
}) => {
  if (isLoading) {
    if (customSkeleton) return <div className={className}>{customSkeleton}</div>;

    switch (loadingSkeleton) {
      case 'table':
        return (
          <div className={className}>
            <TableSkeleton rows={6} />
          </div>
        );
      case 'chart':
        return (
          <div className={className}>
            <ChartSkeleton />
          </div>
        );
      case 'list':
        return (
          <div className={className}>
            <CardListSkeleton count={3} />
          </div>
        );
      case 'card-grid':
      default:
        return (
          <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 ${className}`}>
            <KpiCardSkeleton />
            <KpiCardSkeleton />
            <KpiCardSkeleton />
            <KpiCardSkeleton />
          </div>
        );
    }
  }

  if (isError) {
    return (
      <ErrorState
        message={errorMessage}
        onRetry={onRetry}
        className={className}
      />
    );
  }

  if (isEmpty) {
    return (
      <EmptyState
        icon={emptyIcon}
        title={emptyTitle}
        description={emptyDescription}
        actionText={emptyActionText}
        onAction={onEmptyAction}
        actionLoading={emptyActionLoading}
        secondaryActionText={emptySecondaryActionText}
        onSecondaryAction={onEmptySecondaryAction}
        customAction={emptyAction}
        className={className}
      />
    );
  }

  return <div className={`animate-fade-in ${className}`}>{children}</div>;
};
