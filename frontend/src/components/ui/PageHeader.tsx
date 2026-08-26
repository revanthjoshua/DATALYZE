import React from 'react';

export interface PageHeaderProps {
  stage?: string;
  stageIcon?: React.ReactNode;
  title: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  stage,
  stageIcon,
  title,
  description,
  actions,
  className = '',
}) => {
  return (
    <div
      className={`flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-1 ${className}`}
    >
      <div className="space-y-1">
        {stage && (
          <div className="flex items-center space-x-2 text-xs text-[#6B4226] dark:text-[#8C5E3C] font-bold uppercase tracking-wider font-mono">
            {stageIcon && <span className="shrink-0">{stageIcon}</span>}
            <span>{stage}</span>
          </div>
        )}
        <h1 className="text-xl sm:text-2xl font-extrabold text-neutral-900 dark:text-neutral-100 tracking-tight">
          {title}
        </h1>
        {description && (
          <p className="text-xs sm:text-sm text-neutral-500 dark:text-neutral-400 font-normal max-w-2xl leading-relaxed">
            {description}
          </p>
        )}
      </div>

      {actions && (
        <div className="flex items-center space-x-2.5 shrink-0 self-start sm:self-auto flex-wrap gap-y-2">
          {actions}
        </div>
      )}
    </div>
  );
};
