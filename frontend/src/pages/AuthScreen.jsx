import { useState } from 'react';
import { api } from '../services/api';
import { useToast } from '../contexts/ToastContext';
import { Icons } from '../components/ui/Icons';

export function AuthScreen({ onAuthSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { showToast } = useToast();

  const isPasswordValid = password.length >= 8;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isLogin && !isPasswordValid) {
      showToast('A senha não atende aos requisitos mínimos.', 'error');
      return;
    }
    
    setIsLoading(true);
    try {
      if (isLogin) {
        const data = await api.login(email, password);
        localStorage.setItem('token', data.access_token);
        onAuthSuccess();
      } else {
        await api.register(email, password);
        showToast('Conta criada com sucesso! Faça login para continuar.', 'success');
        setIsLogin(true);
        setPassword('');
      }
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex w-full max-w-5xl bg-zinc-900/80 backdrop-blur-2xl rounded-[2.5rem] border border-zinc-800 shadow-2xl overflow-hidden min-h-[600px] animate-fade-in relative">
      <div className="hidden lg:flex flex-col justify-between w-1/2 p-12 bg-zinc-950/50 border-r border-zinc-800/80 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-indigo-600/10 blur-[100px] rounded-full pointer-events-none -translate-x-1/2 -translate-y-1/2"></div>
        <div className="relative z-10">
          <div className="inline-flex w-14 h-14 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl items-center justify-center shadow-lg shadow-indigo-500/25 border border-white/10 mb-8">
              <Icons.Hardware className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-4xl font-black text-zinc-100 tracking-tight leading-tight mb-4">
            A forma inteligente <br/><span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">de montar seu PC.</span>
          </h1>
          <p className="text-zinc-400 text-lg font-medium leading-relaxed max-w-sm">
            Audite orçamentos, fuja de preços abusivos e descubra as melhores opções do mercado com o poder da Inteligência Artificial.
          </p>
        </div>
        <div className="relative z-10 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20 text-emerald-400"><Icons.Check className="w-4 h-4" /></div>
            <span className="text-sm font-semibold text-zinc-300">Análise Multimodal (PDF, Imagens)</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 text-indigo-400"><Icons.Search className="w-4 h-4" /></div>
            <span className="text-sm font-semibold text-zinc-300">Scraping em Tempo Real nas Lojas</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-purple-500/10 flex items-center justify-center border border-purple-500/20 text-purple-400"><Icons.Brain className="w-4 h-4" /></div>
            <span className="text-sm font-semibold text-zinc-300">Veredito Automático de Custo-Benefício</span>
          </div>
        </div>
      </div>

      <div className="w-full lg:w-1/2 p-8 sm:p-14 flex flex-col justify-center relative">
        <div className="max-w-md w-full mx-auto">
          <div className="mb-10 text-center lg:text-left">
            <div className="lg:hidden inline-flex w-14 h-14 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl items-center justify-center shadow-lg shadow-indigo-500/25 border border-white/10 mb-6">
                <Icons.Hardware className="w-7 h-7 text-white" />
            </div>
            <h2 className="text-3xl font-black text-zinc-100 tracking-tight">
              {isLogin ? 'Bem-vindo de volta' : 'Crie sua Conta'}
            </h2>
            <p className="mt-2 text-sm font-medium text-zinc-400">
              {isLogin ? 'Acesse o seu painel de análises' : 'Junte-se à plataforma e fuja de preços abusivos'}
            </p>
          </div>

          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-5">
              <div>
                <label className="block text-sm font-bold text-zinc-300 mb-2">E-mail corporativo ou pessoal</label>
                <div className="relative">
                  <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
                    className="block w-full rounded-xl border border-zinc-700/60 bg-zinc-950/50 px-4 py-3.5 text-zinc-200 placeholder-zinc-600 focus:border-indigo-500 focus:bg-zinc-900 focus:ring-1 focus:ring-indigo-500 transition-all outline-none"
                    placeholder="voce@exemplo.com" />
                </div>
              </div>
              
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-sm font-bold text-zinc-300">Sua senha</label>
                </div>
                <div className="relative">
                  <input type={showPassword ? "text" : "password"} required value={password} onChange={(e) => setPassword(e.target.value)}
                    className={`block w-full rounded-xl border bg-zinc-950/50 px-4 py-3.5 text-zinc-200 placeholder-zinc-600 focus:bg-zinc-900 focus:ring-1 transition-all outline-none pr-12
                      ${!isLogin && password.length > 0 && !isPasswordValid ? 'border-red-500/50 focus:border-red-500 focus:ring-red-500' : 'border-zinc-700/60 focus:border-indigo-500 focus:ring-indigo-500'}
                    `}
                    placeholder="••••••••" />
                  <button type="button" onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-4 flex items-center text-zinc-500 hover:text-zinc-300 transition-colors"
                  >
                    {showPassword ? <Icons.EyeOff className="w-5 h-5"/> : <Icons.Eye className="w-5 h-5"/>}
                  </button>
                </div>
                {!isLogin && (
                  <div className="mt-3 flex items-center gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full transition-colors duration-300 ${password.length === 0 ? 'bg-zinc-700' : isPasswordValid ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]' : 'bg-red-500'}`}></div>
                    <span className={`text-xs font-semibold transition-colors duration-300 ${password.length === 0 ? 'text-zinc-500' : isPasswordValid ? 'text-emerald-400' : 'text-red-400'}`}>
                      Pelo menos 8 caracteres
                    </span>
                  </div>
                )}
              </div>
            </div>

            <button type="submit" disabled={isLoading}
              className="w-full flex justify-center items-center py-4 px-4 border border-transparent rounded-xl shadow-[0_0_20px_rgba(79,70,229,0.15)] text-sm font-black text-white bg-indigo-600 hover:bg-indigo-500 hover:shadow-[0_0_30px_rgba(79,70,229,0.3)] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 focus:ring-offset-zinc-950 disabled:opacity-50 transition-all mt-8">
              {isLoading ? <Icons.Spinner className="w-5 h-5" /> : (isLogin ? 'Entrar no Painel' : 'Finalizar Cadastro')}
            </button>
          </form>

          <div className="mt-8 pt-8 border-t border-zinc-800/80 text-center">
            <p className="text-sm font-medium text-zinc-400">
              {isLogin ? 'Ainda não tem conta?' : 'Já possui conta?'}
              <button onClick={() => { setIsLogin(!isLogin); setPassword(''); setEmail(''); }} className="ml-2 font-bold text-indigo-400 hover:text-indigo-300 transition-colors focus:outline-none">
                {isLogin ? 'Cadastre-se grátis' : 'Fazer login'}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}