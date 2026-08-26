import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastItem {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
  durationMs?: number;
}

interface ToastContextType {
  toast: {
    success: (message: string, title?: string, durationMs?: number) => void;
    error: (message: string, title?: string, durationMs?: number) => void;
    warning: (message: string, title?: string, durationMs?: number) => void;
    info: (message: string, title?: string, durationMs?: number) => void;
  };
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

const typeIcons: Record<ToastType, React.ReactNode> = {
  success: <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />,
  error: <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />,
  warning: <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />,
  info: <Info className="w-4 h-4 text-blue-500 shrink-0" />,
};

const typeBorders: Record<ToastType, string> = {
  success: 'border-emerald-200 dark:border-emerald-900/60',
  error: 'border-red-200 dark:border-red-900/60',
  warning: 'border-amber-200 dark:border-amber-900/60',
  info: 'border-blue-200 dark:border-blue-900/60',
};

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    (type: ToastType, message: string, title?: string, durationMs: number = 4000) => {
      const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      const newToast: ToastItem = { id, type, title, message, durationMs };

      setToasts((prev) => [...prev, newToast]);

      if (durationMs > 0) {
        setTimeout(() => {
          removeToast(id);
        }, durationMs);
      }
    },
    [removeToast]
  );

  const toast = {
    success: (message: string, title?: string, durationMs?: number) =>
      addToast('success', message, title, durationMs),
    error: (message: string, title?: string, durationMs?: number) =>
      addToast('error', message, title, durationMs),
    warning: (message: string, title?: string, durationMs?: number) =>
      addToast('warning', message, title, durationMs),
    info: (message: string, title?: string, durationMs?: number) =>
      addToast('info', message, title, durationMs),
  };

  return (
    <ToastContext.Provider value={{ toast, removeToast }}>
      {children}

      {/* Floating Stacked Toasts Container */}
      <div
        aria-live="assertive"
        className="fixed bottom-4 right-4 z-50 flex flex-col space-y-2 max-w-sm w-full pointer-events-none"
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`pointer-events-auto flex items-start justify-between gap-3 p-3.5 bg-white dark:bg-[#15171C] border ${typeBorders[t.type]} shadow-xl rounded-xl animate-slide-up transition-all`}
          >
            <div className="flex items-start space-x-2.5 overflow-hidden">
              <div className="mt-0.5">{typeIcons[t.type]}</div>
              <div className="space-y-0.5 overflow-hidden">
                {t.title && (
                  <h4 className="text-xs font-bold text-neutral-900 dark:text-neutral-100 tracking-tight">
                    {t.title}
                  </h4>
                )}
                <p className="text-xs text-neutral-600 dark:text-neutral-300 font-normal leading-relaxed">
                  {t.message}
                </p>
              </div>
            </div>

            <button
              onClick={() => removeToast(t.id)}
              className="text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200 transition-colors p-0.5 shrink-0 cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context.toast;
};
