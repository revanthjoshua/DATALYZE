import React from 'react';

export type BadgeVariant =
  | 'critical'
  | 'warning'
  | 'healthy'
  | 'info'
  | 'brand'
  | 'neutral';

export type BadgeSize = 'xs' | 'sm' | 'md';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
  pulse?: boolean;
}

const variantStyles: Record<BadgeVariant, { bg: string; dot: string }> = {
  critical: {
    bg: 'bg-red-50 text-red-600 border-red-200 dark:bg-red-950/40 dark:text-red-400 dark:border-red-900/60',
    dot: 'bg-red-500',
  },
  warning: {
    bg: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-900/60',
    dot: 'bg-amber-500',
  },
  healthy: {
    bg: 'bg-emerald-50 text-emerald-600 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-900/60',
    dot: 'bg-emerald-500',
  },
  info: {
    bg: 'bg-blue-50 text-blue-600 border-blue-200 dark:bg-blue-950/40 dark:text-blue-400 dark:border-blue-900/60',
    dot: 'bg-blue-500',
  },
  brand: {
    bg: 'bg-[#F4ECE4] text-[#6B4226] border-[#E8D6C7] dark:bg-[#271910] dark:text-[#D5B79F] dark:border-[#55331C]',
    dot: 'bg-[#6B4226] dark:bg-[#8C5E3C]',
  },
  neutral: {
    bg: 'bg-neutral-100 text-neutral-600 border-neutral-200 dark:bg-neutral-800 dark:text-neutral-300 dark:border-neutral-700',
    dot: 'bg-neutral-400',
  },
};

const sizeStyles: Record<BadgeSize, string> = {
  xs: 'text-[10px] px-1.5 py-0.2 rounded font-mono',
  sm: 'text-[11px] px-2.5 py-0.5 rounded-full font-semibold',
  md: 'text-xs px-3 py-1 rounded-full font-semibold',
};

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'sm',
  dot = false,
  pulse = false,
  className = '',
  ...props
}) => {
  const currentVariant = variantStyles[variant];

  return (
    <span
      className={`inline-flex items-center gap-1.5 border uppercase tracking-wider ${currentVariant.bg} ${sizeStyles[size]} ${className}`}
      {...props}
    >
      {dot && (
        <span className="relative flex h-1.5 w-1.5 shrink-0">
          {pulse && (
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${currentVariant.dot}`}
            />
          )}
          <span className={`relative inline-flex rounded-full h-1.5 w-1.5 ${currentVariant.dot}`} />
        </span>
      )}
      {children}
    </span>
  );
};
