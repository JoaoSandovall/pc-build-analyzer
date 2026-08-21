import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { Icons } from '../components/ui/Icons';

const ToastContext = createContext({});

export const ToastProvider = ({ children }) => {
  const [toast, setToast] = useState({ message: '', type: '' });

  const showToast = useCallback((message, type = 'info') => {
    setToast({ message, type });
  }, []);

  const closeToast = useCallback(() => {
    setToast({ message: '', type: '' });
  }, []);

  useEffect(() => {
    if (toast.message) {
      const timer = setTimeout(closeToast, 5000);
      return () => clearTimeout(timer);
    }
  }, [toast.message, closeToast]);

  const bgColors = {
    error: 'bg-red-950/90 border-red-900/50 text-red-200',
    success: 'bg-emerald-950/90 border-emerald-900/50 text-emerald-200',
    info: 'bg-indigo-950/90 border-indigo-900/50 text-indigo-200'
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {toast.message && (
        <div className={`fixed bottom-6 right-6 z-50 flex items-center p-4 mb-4 rounded-xl border shadow-2xl backdrop-blur-md animate-fade-in ${bgColors[toast.type] || bgColors.info}`}>
          {toast.type === 'info' && <Icons.Spinner className="h-4 w-4 mr-3 text-indigo-400" />}
          {toast.type === 'success' && <Icons.Check className="w-4 h-4 mr-3 text-emerald-400" />}
          {toast.type === 'error' && <Icons.X className="w-4 h-4 mr-3 text-red-400" />}
          <div className="text-sm font-medium mr-4">{toast.message}</div>
          <button onClick={closeToast} className="ml-auto opacity-70 hover:opacity-100 transition-opacity">
            <Icons.X className="w-4 h-4 text-current" />
          </button>
        </div>
      )}
    </ToastContext.Provider>
  );
};

export const useToast = () => useContext(ToastContext);