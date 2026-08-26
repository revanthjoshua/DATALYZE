import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverable?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  hoverable = false,
  className = '',
  ...props
}) => {
  return (
    <div
      className={`bg-white dark:bg-[#15171C] border border-neutral-200 dark:border-neutral-800 rounded-2xl shadow-xs transition-all duration-150 ${
        hoverable
          ? 'hover:border-[#6B4226]/40 dark:hover:border-[#8C5E3C]/50 hover:shadow-md'
          : ''
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className = '',
  ...props
}) => {
  return (
    <div
      className={`p-4 sm:p-5 border-b border-neutral-100 dark:border-neutral-800/80 flex items-center justify-between gap-4 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  children,
  className = '',
  ...props
}) => {
  return (
    <h3
      className={`text-sm sm:text-base font-bold text-neutral-900 dark:text-neutral-100 tracking-tight ${className}`}
      {...props}
    >
      {children}
    </h3>
  );
};

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({
  children,
  className = '',
  ...props
}) => {
  return (
    <p
      className={`text-xs text-neutral-500 dark:text-neutral-400 font-normal leading-relaxed ${className}`}
      {...props}
    >
      {children}
    </p>
  );
};

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className = '',
  ...props
}) => {
  return (
    <div className={`p-4 sm:p-5 ${className}`} {...props}>
      {children}
    </div>
  );
};

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className = '',
  ...props
}) => {
  return (
    <div
      className={`p-3.5 sm:p-4 bg-neutral-50/50 dark:bg-neutral-900/40 border-t border-neutral-100 dark:border-neutral-800/80 rounded-b-2xl flex items-center justify-between gap-3 text-xs ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
