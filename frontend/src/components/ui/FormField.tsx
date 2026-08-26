import React from 'react';
import { AlertCircle } from 'lucide-react';

export interface FormFieldProps {
  label?: string;
  required?: boolean;
  error?: string | null;
  helperText?: string;
  children: React.ReactNode;
  className?: string;
}

export const FormField: React.FC<FormFieldProps> = ({
  label,
  required = false,
  error,
  helperText,
  children,
  className = '',
}) => {
  return (
    <div className={`space-y-1.5 ${className}`}>
      {label && (
        <label className="block text-xs font-semibold text-neutral-700 dark:text-neutral-300 uppercase tracking-wider font-mono">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}

      {children}

      {error ? (
        <div className="flex items-center space-x-1.5 text-xs text-red-600 dark:text-red-400 font-medium animate-fade-in pt-0.5">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
          <span>{error}</span>
        </div>
      ) : helperText ? (
        <p className="text-[11px] text-neutral-500 dark:text-neutral-400 leading-relaxed font-normal">
          {helperText}
        </p>
      ) : null}
    </div>
  );
};

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  hasError?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ hasError = false, leftIcon, rightIcon, className = '', ...props }, ref) => {
    return (
      <div className="relative flex items-center">
        {leftIcon && (
          <div className="absolute left-3 text-neutral-400 pointer-events-none shrink-0">
            {leftIcon}
          </div>
        )}
        <input
          ref={ref}
          className={`w-full py-2 text-xs bg-neutral-50/50 dark:bg-neutral-900 border rounded-xl text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 transition-all font-sans ${
            leftIcon ? 'pl-9' : 'pl-3.5'
          } ${rightIcon ? 'pr-9' : 'pr-3.5'} ${
            hasError
              ? 'border-red-400 dark:border-red-500 focus:border-red-500 focus:ring-2 focus:ring-red-500/20'
              : 'border-neutral-200 dark:border-neutral-700/80 focus:border-[#6B4226] dark:focus:border-[#8C5E3C] focus:ring-2 focus:ring-[#6B4226]/20'
          } focus:outline-none ${className}`}
          {...props}
        />
        {rightIcon && (
          <div className="absolute right-3 text-neutral-400 shrink-0">
            {rightIcon}
          </div>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  hasError?: boolean;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ hasError = false, children, className = '', ...props }, ref) => {
    return (
      <select
        ref={ref}
        className={`w-full px-3 py-2 text-xs bg-neutral-50/50 dark:bg-neutral-900 border rounded-xl text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 transition-all font-sans cursor-pointer ${
          hasError
            ? 'border-red-400 dark:border-red-500 focus:border-red-500 focus:ring-2 focus:ring-red-500/20'
            : 'border-neutral-200 dark:border-neutral-700/80 focus:border-[#6B4226] dark:focus:border-[#8C5E3C] focus:ring-2 focus:ring-[#6B4226]/20'
        } focus:outline-none ${className}`}
        {...props}
      >
        {children}
      </select>
    );
  }
);

Select.displayName = 'Select';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  hasError?: boolean;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ hasError = false, className = '', ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={`w-full p-3 text-xs bg-neutral-50/50 dark:bg-neutral-900 border rounded-xl text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 transition-all font-sans resize-y min-h-[80px] ${
          hasError
            ? 'border-red-400 dark:border-red-500 focus:border-red-500 focus:ring-2 focus:ring-red-500/20'
            : 'border-neutral-200 dark:border-neutral-700/80 focus:border-[#6B4226] dark:focus:border-[#8C5E3C] focus:ring-2 focus:ring-[#6B4226]/20'
        } focus:outline-none ${className}`}
        {...props}
      />
    );
  }
);

Textarea.displayName = 'Textarea';
