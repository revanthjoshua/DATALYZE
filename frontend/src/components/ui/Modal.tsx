import React, { useEffect } from 'react';
import { X } from 'lucide-react';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '4xl' | '5xl' | '6xl' | 'full';
  className?: string;
}

const maxWidthStyles = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  '2xl': 'max-w-2xl',
  '4xl': 'max-w-4xl',
  '5xl': 'max-w-5xl',
  '6xl': 'max-w-6xl',
  full: 'max-w-[95vw]',
};

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  icon,
  children,
  maxWidth = 'lg',
  className = '',
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-neutral-950/60 backdrop-blur-xs animate-fade-in">
      <div
        className={`w-full ${maxWidthStyles[maxWidth]} bg-white dark:bg-[#15171C] border border-neutral-200 dark:border-neutral-800 shadow-2xl rounded-2xl overflow-hidden animate-slide-up flex flex-col max-h-[90vh] ${className}`}
      >
        {/* Header */}
        {(title || icon) && (
          <div className="p-4 sm:p-5 border-b border-neutral-100 dark:border-neutral-800/80 flex items-center justify-between gap-3 bg-neutral-50/50 dark:bg-neutral-900/30 shrink-0">
            <div className="flex items-center space-x-2.5">
              {icon && <span className="text-[#6B4226] dark:text-[#8C5E3C]">{icon}</span>}
              <div>
                {title && (
                  <h3 className="text-sm sm:text-base font-bold text-neutral-900 dark:text-neutral-100 tracking-tight">
                    {title}
                  </h3>
                )}
                {description && (
                  <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5 font-normal">
                    {description}
                  </p>
                )}
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Content */}
        <div className="p-4 sm:p-6 overflow-y-auto flex-1">{children}</div>
      </div>
    </div>
  );
};
