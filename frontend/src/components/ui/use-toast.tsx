'use client';

import { useState, useEffect, createContext, useContext } from 'react';

interface Toast {
  id: string;
  title: string;
  description?: string;
  variant?: 'default' | 'success' | 'error' | 'warning';
}

interface ToastContextValue {
  toasts: Toast[];
  toast: (toast: Omit<Toast, 'id'>) => void;
  dismiss: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = (newToast: Omit<Toast, 'id'>) => {
    const id = Date.now().toString();
    setToasts((prev) => [...prev, { ...newToast, id }]);

    // Auto dismiss after 5 seconds
    setTimeout(() => {
      dismiss(id);
    }, 5000);
  };

  const dismiss = (id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  return (
    <ToastContext.Provider value={{ toasts, toast, dismiss }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 space-y-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`
              max-w-sm p-4 rounded-lg shadow-lg transition-all duration-300 transform
              ${
                toast.variant === 'error'
                  ? 'bg-red-50 border border-red-200 text-red-900'
                  : toast.variant === 'success'
                  ? 'bg-green-50 border border-green-200 text-green-900'
                  : toast.variant === 'warning'
                  ? 'bg-yellow-50 border border-yellow-200 text-yellow-900'
                  : 'bg-white border border-gray-200 text-gray-900'
              }
            `}
          >
            <div className="flex items-start">
              <div className="flex-1">
                <h4 className="font-medium">{toast.title}</h4>
                {toast.description && (
                  <p className="mt-1 text-sm opacity-90">{toast.description}</p>
                )}
              </div>
              <button
                onClick={() => dismiss(toast.id)}
                className="ml-4 text-gray-400 hover:text-gray-600"
              >
                <svg
                  className="h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    // Return a dummy implementation if provider is not found
    return {
      toast: (toast: Omit<Toast, 'id'>) => {
        console.log('Toast:', toast);
      },
      toasts: [],
      dismiss: () => {},
    };
  }
  return context;
}