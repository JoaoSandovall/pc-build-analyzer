import { Icons } from '../ui/Icons';

export const ProcessingModal = ({ step }) => {
  if (step === 0) return null;

  const stepsConfig = [
    { id: 1, title: 'Upload Seguro (S3)', desc: 'Enviando arquivo criptografado...', icon: Icons.Cloud },
    { id: 2, title: 'Inteligência Artificial', desc: 'Lendo peças e extraindo preços...', icon: Icons.Brain },
    { id: 3, title: 'Gerando Dashboard', desc: 'Auditando componentes...', icon: Icons.Dashboard },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/80 backdrop-blur-md animate-fade-in px-4">
      <div className="bg-zinc-900 border border-zinc-800 p-8 rounded-3xl shadow-2xl max-w-sm w-full">
        <div className="flex flex-col items-center text-center mb-8">
            <div className="w-16 h-16 bg-indigo-500/10 rounded-2xl flex items-center justify-center border border-indigo-500/20 mb-4 animate-pulse">
                {step >= 4 ? <Icons.Check className="w-8 h-8 !text-emerald-400 !mr-0" /> : <Icons.Hardware className="w-8 h-8 text-indigo-400" />}
            </div>
            <h3 className="text-xl font-bold text-zinc-100">Processando Documento</h3>
            <p className="text-sm text-zinc-400 mt-1">Por favor, aguarde não feche a janela.</p>
        </div>

        <div className="space-y-6">
          {stepsConfig.map((s) => {
            const isActive = step === s.id;
            const isPast = step > s.id;
            const Icon = s.icon;

            return (
              <div key={s.id} className="flex items-start gap-4">
                <div className={`mt-0.5 w-8 h-8 rounded-full flex items-center justify-center shrink-0 border transition-colors duration-300 ${
                  isActive ? 'bg-indigo-500/20 border-indigo-500 text-indigo-400 shadow-[0_0_15px_rgba(79,70,229,0.3)]' : 
                  isPast ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400' : 
                  'bg-zinc-950 border-zinc-800 text-zinc-600'
                }`}>
                  {isPast ? <Icons.Check className="!mr-0 w-4 h-4" /> : isActive ? <Icons.Spinner className="w-4 h-4" /> : <Icon />}
                </div>
                <div className="flex flex-col">
                  <span className={`text-sm font-bold transition-colors ${isActive || isPast ? 'text-zinc-200' : 'text-zinc-600'}`}>
                    {s.title}
                  </span>
                  <span className={`text-xs transition-colors ${isActive ? 'text-indigo-300' : 'text-zinc-600'}`}>
                    {isPast ? 'Concluído' : isActive ? s.desc : 'Aguardando...'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};