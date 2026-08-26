import React from 'react';
import { Loader2 } from 'lucide-react';

export type ButtonVariant = 'primary' | 'secondary' | 'destructive' | 'outline' | 'ghost' | 'link';
export type ButtonSize = 'xs' | 'sm' | 'md' | 'lg';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-[#6B4226] hover:bg-[#55331C] dark:bg-[#7A4B2C] dark:hover:bg-[#6B4226] text-white border border-black/15 dark:border-white/10 shadow-xs active:translate-y-[1px]',
  secondary:
    'bg-white dark:bg-[#15171C] text-neutral-900 dark:text-neutral-100 border border-neutral-200 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800 hover:border-[#6B4226]/40 dark:hover:border-[#8C5E3C]/50 shadow-xs active:translate-y-[1px]',
  destructive:
    'bg-red-600 hover:bg-red-700 text-white border border-red-700 shadow-xs active:translate-y-[1px]',
  outline:
    'bg-transparent border border-neutral-300 dark:border-neutral-700 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 active:translate-y-[1px]',
  ghost:
    'bg-transparent text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 hover:text-neutral-900 dark:hover:text-neutral-100',
  link:
    'bg-transparent text-[#6B4226] dark:text-[#8C5E3C] hover:underline p-0 h-auto font-medium',
};

const sizeStyles: Record<ButtonSize, string> = {
  xs: 'text-[11px] px-2 py-1 rounded-md gap-1 font-medium',
  sm: 'text-xs px-3 py-1.5 rounded-lg gap-1.5 font-semibold',
  md: 'text-xs sm:text-sm px-4 py-2 rounded-xl gap-2 font-semibold',
  lg: 'text-sm sm:text-base px-5 py-2.5 rounded-xl gap-2.5 font-bold',
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = 'secondary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      className = '',
      disabled,
      ...props
    },
    ref
  ) => {
    const isLink = variant === 'link';
    const baseClasses =
      'inline-flex items-center justify-center transition-all duration-150 select-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none';

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={`${baseClasses} ${variantStyles[variant]} ${!isLink ? sizeStyles[size] : ''} ${className}`}
        {...props}
      >
        {isLoading ? (
          <>
            <Loader2 className="w-3.5 h-3.5 animate-spin shrink-0" />
            <span>{children}</span>
          </>
        ) : (
          <>
            {leftIcon && <span className="shrink-0">{leftIcon}</span>}
            {children && <span>{children}</span>}
            {rightIcon && <span className="shrink-0">{rightIcon}</span>}
          </>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';
