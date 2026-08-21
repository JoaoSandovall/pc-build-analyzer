import { Icons } from './ui/Icons';
import { formatPrice, formatDate } from '../utils/formatters';

export const HistoryView = ({ budgets, isLoading, onOpen, onDeleteRequest }) => {
  return (
    <section className="mt-14 border-t border-zinc-800/80 pt-10">
      <div className="flex items-center justify-between mb-6">
        <div>
            <h3 className="text-xl font-bold text-zinc-100 tracking-tight">Histórico de Análises</h3>
            <p className="text-sm font-medium text-zinc-500 mt-1">Seus orçamentos processados anteriormente</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3">
        {isLoading && <div className="p-6 text-center text-sm font-medium text-zinc-500 bg-zinc-900/30 rounded-2xl border border-zinc-800/50">Carregando histórico...</div>}
        {!isLoading && budgets.length === 0 && <div className="p-6 text-center text-sm font-medium text-zinc-500 bg-zinc-900/30 rounded-2xl border border-zinc-800/50">Nenhum orçamento encontrado.</div>}
        
        {budgets.map((budget) => (
          <div 
            key={budget.budget_id} 
            onClick={() => onOpen(budget.budget_id)}
            className="group flex w-full items-center justify-between gap-4 rounded-2xl border border-zinc-800 bg-zinc-900/40 p-4 sm:p-5 text-left hover:border-indigo-500/50 hover:bg-zinc-800/80 transition-all shadow-sm cursor-pointer"
          >
            <div className="min-w-0 flex-1 pr-4">
              <span className="block truncate text-sm font-bold text-zinc-200 group-hover:text-indigo-300 transition-colors">{budget.nome_arquivo}</span>
              <div className="flex items-center gap-3 mt-2">
                  <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider bg-zinc-950 px-2 py-0.5 rounded border border-zinc-800">{budget.status}</span>
                  <span className="text-[11px] font-medium text-zinc-600">{formatDate(budget.criado_em)}</span>
              </div>
            </div>

            <div className="flex items-center shrink-0">
              
              <span className="shrink-0 text-lg font-black text-indigo-400 bg-indigo-500/10 px-4 py-2 rounded-xl border border-indigo-500/20">
                {formatPrice(budget.valor_total_orcamento)}
              </span>
              
              <div className="overflow-hidden flex items-center transition-all duration-300 ease-out max-w-0 opacity-0 group-hover:max-w-[60px] group-hover:opacity-100 group-hover:ml-3">
                  <button 
                    onClick={(e) => { e.stopPropagation(); onDeleteRequest(budget.budget_id); }}
                    className="p-2.5 rounded-xl bg-zinc-950 border border-zinc-800 text-zinc-500 hover:text-red-400 hover:bg-red-950 hover:border-red-900/50 transition-colors shadow-md shrink-0"
                    title="Excluir Orçamento"
                  >
                      <Icons.Trash />
                  </button>
              </div>

            </div>
          </div>
        ))}
      </div>
    </section>
  );
};