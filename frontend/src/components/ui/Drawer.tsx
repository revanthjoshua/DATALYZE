import React, { useEffect } from 'react';
import { X } from 'lucide-react';

export interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  subtitle?: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  width?: 'sm' | 'md' | 'lg' | 'xl';
  footer?: React.ReactNode;
}

const widthStyles = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
};

export const Drawer: React.FC<DrawerProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  icon,
  children,
  width = 'lg',
  footer,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden animate-fade-in">
      {/* Backdrop */}
      <div
        onClick={onClose}
        className="fixed inset-0 bg-neutral-950/60 backdrop-blur-xs transition-opacity"
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div
          className={`w-screen ${widthStyles[width]} bg-white dark:bg-[#15171C] border-l border-neutral-200 dark:border-neutral-800 shadow-2xl flex flex-col justify-between transform transition-transform duration-200 ease-out animate-slide-left`}
        >
          {/* Header */}
          <div className="p-4 sm:p-5 border-b border-neutral-100 dark:border-neutral-800/80 flex items-center justify-between gap-3 bg-neutral-50/50 dark:bg-neutral-900/30">
            <div className="flex items-center space-x-2.5 overflow-hidden">
              {icon && <span className="text-[#6B4226] dark:text-[#8C5E3C] shrink-0">{icon}</span>}
              <div className="overflow-hidden">
                {title && (
                  <h3 className="text-sm sm:text-base font-bold text-neutral-900 dark:text-neutral-100 truncate tracking-tight">
                    {title}
                  </h3>
                )}
                {subtitle && (
                  <p className="text-xs text-neutral-500 dark:text-neutral-400 truncate mt-0.5 font-normal">
                    {subtitle}
                  </p>
                )}
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors shrink-0 cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Body Content */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5">
            {children}
          </div>

          {/* Optional Footer */}
          {footer && (
            <div className="p-4 bg-neutral-50/50 dark:bg-neutral-900/40 border-t border-neutral-100 dark:border-neutral-800/80 flex items-center justify-end gap-2.5">
              {footer}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
