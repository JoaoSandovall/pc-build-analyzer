import { Component } from 'react';
import { Icons } from './ui/Icons';

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Erro capturado pelo ErrorBoundary:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-4">
          <div className="bg-red-950/30 border border-red-900/50 p-8 rounded-3xl max-w-lg text-center">
            <Icons.Warn className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h1 className="text-xl font-bold text-red-400 mb-2">Ops! Algo deu errado.</h1>
            <p className="text-sm text-red-300/80 mb-6">
              {this.state.error?.message || "Erro interno no React."}
            </p>
            <button 
              onClick={() => window.location.reload()} 
              className="bg-red-600 hover:bg-red-500 text-white px-6 py-2 rounded-xl font-bold transition-colors"
            >
              Recarregar Página
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}