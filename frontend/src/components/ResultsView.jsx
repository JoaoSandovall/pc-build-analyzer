import { useRef } from 'react';
import { Icons } from './ui/Icons';
import { Badge } from './ui/Badge';
import { formatPrice } from '../utils/formatters';

export const ResultsView = ({ data, onFindPrice, loadingItem }) => {
  const lastClickTime = useRef(0);

  if (!data || !data.itens) return null;

  const getVereditoConfig = (veredito) => {
    switch(veredito) {
      case 'JUSTO': return { color: 'emerald', label: 'Preço Justo', icon: Icons.Check };
      case 'ACIMA_DA_MEDIA': return { color: 'yellow', label: 'Acima da Média', icon: Icons.Warn };
      case 'MUITO_ACIMA': return { color: 'red', label: 'Muito Caro', icon: Icons.X };
      default: return { color: 'zinc', label: 'Sem Comparação', icon: null };
    }
  };

  return (
    <div className="mt-14 animate-fade-in border-t border-zinc-800/80 pt-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div className="flex items-center space-x-4">
            <div className="p-3 bg-indigo-500/10 rounded-xl border border-indigo-500/20 shadow-inner">
                <Icons.Hardware className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
                <h3 className="text-2xl font-bold text-zinc-100 tracking-tight">Análise da Build</h3>
                <p className="text-sm font-medium text-zinc-500 mt-0.5">Comparação com o mercado nacional</p>
            </div>
        </div>
      </div>
      
      <div className="bg-zinc-900/40 rounded-3xl border border-zinc-800/80 shadow-2xl backdrop-blur-md overflow-hidden">
        <div className="p-6 sm:p-8 bg-zinc-950/50 border-b border-zinc-800/80 flex flex-col md:flex-row md:justify-between md:items-center gap-6">
            <div>
                <span className="text-[11px] font-extrabold text-zinc-500 uppercase tracking-widest block mb-1.5">Valor Original do Orçamento</span>
                <span className="text-3xl font-black text-zinc-100 tracking-tight">
                    {formatPrice(data.valor_total_orcamento)}
                </span>
            </div>
            
            {data.economia_potencial > 0 ? (
                <div className="flex flex-col md:items-end bg-gradient-to-br from-emerald-500/10 to-emerald-900/10 p-4 rounded-2xl border border-emerald-500/20 shadow-inner">
                    <span className="text-[11px] font-extrabold text-emerald-500/80 uppercase tracking-widest block mb-1">Economia Possível</span>
                    <span className="text-2xl font-black text-emerald-400 tracking-tight">
                        {formatPrice(data.economia_potencial)}
                    </span>
                </div>
            ) : (
                <div className="flex flex-col md:items-end">
                    <span className="text-[11px] font-extrabold text-zinc-600 uppercase tracking-widest block mb-1">Status da Build</span>
                    <Badge color="emerald">Ótimo Custo-Benefício</Badge>
                </div>
            )}
        </div>
        
        <div className="divide-y divide-zinc-800/40">
          {data.itens.map((item) => {
            const vConfig = getVereditoConfig(item.veredito);
            const VereditoIcon = vConfig.icon;
            
            return (
            <div key={item.item_id} className="p-6 sm:p-8 hover:bg-zinc-800/20 transition-colors flex flex-col xl:flex-row gap-8 justify-between items-start xl:items-center group">
              
              <div className="flex flex-col w-full xl:w-5/12 min-w-0">
                <div className="flex items-center gap-3 mb-3">
                  <Badge color="zinc">{item.categoria}</Badge>
                  {item.loja_origem && <span className="text-[10px] font-bold text-zinc-600 uppercase truncate">Loja: {item.loja_origem}</span>}
                </div>
                <p className="text-sm font-semibold text-zinc-200 leading-relaxed truncate whitespace-normal line-clamp-3">
                    {item.descricao_original}
                </p>
              </div>

              <div className="w-full xl:w-7/12 flex justify-start xl:justify-end min-w-0 mt-4 xl:mt-0">
                {item.status_scraping === "pendente" || item.status_scraping === "erro" ? (
                    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 w-full sm:w-auto bg-zinc-950/30 p-3 sm:p-2 sm:pr-2 sm:pl-5 rounded-2xl border border-zinc-800/50">
                        <div className="flex flex-col mr-2">
                            <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest mb-0.5">Preço Físico</span>
                            <span className="text-sm font-bold text-zinc-300">{formatPrice(item.preco_orcamento)}</span>
                        </div>
                        
                        <button 
                            onClick={(e) => {
                                const agora = Date.now();
                                if (agora - lastClickTime.current > 1500) {
                                    lastClickTime.current = agora;
                                    onFindPrice(item.item_id);
                                }
                            }}
                            disabled={loadingItem === item.item_id}
                            className="flex items-center justify-center w-full sm:w-auto px-5 py-3 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl transition-all disabled:opacity-60 disabled:cursor-wait shadow-lg whitespace-nowrap"
                        >
                            {loadingItem === item.item_id ? (
                                <><Icons.Spinner className="h-4 w-4 mr-2" /> Buscando nas Lojas...</>
                            ) : (
                                <><Icons.Search /> Comparar Online</>
                            )}
                        </button>
                        {item.status_scraping === "erro" && loadingItem !== item.item_id &&(
                            <span className="text-[11px] font-bold text-red-400 bg-red-400/10 px-3 py-1.5 rounded-lg border border-red-500/20 whitespace-nowrap">Falha. Tentar Novamente</span>
                        )}
                    </div>
                ) : (
                    <div className="flex flex-col w-full sm:w-auto gap-3 min-w-0">
                      <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto_1fr_auto] items-center gap-0 w-full sm:w-auto bg-zinc-950 rounded-2xl border border-zinc-800/80 shadow-inner overflow-hidden">
                          
                          <div className="flex flex-col px-5 py-4 bg-zinc-900/30">
                              <span className="text-[10px] uppercase tracking-widest text-zinc-500 font-bold mb-1">Seu Orçamento</span>
                              <span className={`text-sm font-black whitespace-nowrap ${item.veredito === 'MUITO_ACIMA' ? 'text-red-400/80 line-through decoration-red-500/50' : 'text-zinc-300'}`}>
                                  {formatPrice(item.preco_orcamento)}
                              </span>
                          </div>

                          <div className="hidden sm:flex text-zinc-700/50 justify-center">
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" /></svg>
                          </div>
                          
                          <div className="flex flex-col px-5 py-4 border-t sm:border-t-0 border-zinc-800/50">
                              <span className="text-[10px] uppercase tracking-widest text-zinc-500 font-bold mb-1">Na Internet</span>
                              <span className="text-base font-black text-zinc-100 whitespace-nowrap">
                                  {item.menor_preco_mercado ? formatPrice(item.menor_preco_mercado) : "N/A"}
                              </span>
                          </div>
                          
                          <div className="flex items-center justify-center p-4 sm:pr-5 border-t sm:border-t-0 border-zinc-800/50">
                              <Badge color={vConfig.color}>
                                  <span className="flex items-center whitespace-nowrap">
                                      {VereditoIcon && <VereditoIcon />} {vConfig.label}
                                  </span>
                              </Badge>
                          </div>
                      </div>

                      {(() => {
                          const maisBarato = item.precos_mercado?.reduce((m, p) => (!m || p.preco < m.preco ? p : m), null);
                          if (!maisBarato) return null;
                          return (
                              <a href={maisBarato.url_produto} target="_blank" rel="noopener noreferrer"
                                  className="text-[11px] font-medium text-zinc-500 hover:text-indigo-400 transition-colors px-2 truncate block w-full max-w-full sm:max-w-md xl:max-w-lg"
                                  title="Abrir página da loja para confirmar o modelo">
                                  Encontrado em {maisBarato.loja}: <span className="underline decoration-zinc-700 underline-offset-2">{maisBarato.nome_produto_encontrado || "Ver página"}</span> ↗
                              </a>
                          );
                      })()}
                    </div>
                )}
              </div>
            </div>
          )})}
        </div>
      </div>
    </div>
  );
};