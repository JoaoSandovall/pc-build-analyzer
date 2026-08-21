import { useState, useEffect } from 'react';
import { AuthScreen } from './pages/AuthScreen';
import { Dashboard } from './pages/Dashboard';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ToastProvider, useToast } from './contexts/ToastContext';

function AppContent() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('token'));
  const { showToast } = useToast();

  useEffect(() => {
    const handleSessionExpired = () => {
      localStorage.removeItem('token');
      setIsAuthenticated(false);
      showToast('Sua sessão expirou por inatividade. Faça login novamente.', 'error');
    };

    window.addEventListener('session-expired', handleSessionExpired);
    return () => window.removeEventListener('session-expired', handleSessionExpired);
  }, [showToast]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
  };

  return (
    <div className="min-h-screen bg-zinc-950 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 font-sans antialiased text-zinc-200">
      <div className="fixed inset-0 bg-gradient-to-br from-zinc-950 via-zinc-950/95 to-zinc-900 pointer-events-none -z-10"></div>
      
      {isAuthenticated ? (
        <Dashboard onLogout={handleLogout} />
      ) : (
        <div className="flex items-center justify-center w-full animate-fade-in z-10 relative">
          <AuthScreen onAuthSuccess={() => setIsAuthenticated(true)} />
        </div>
      )}
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <AppContent />
      </ToastProvider>
    </ErrorBoundary>
  );
}