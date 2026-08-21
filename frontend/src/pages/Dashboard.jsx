import { useDashboardLogic } from '../hooks/useDashboardLogic';
import { UploadZone } from '../components/UploadZone';
import { ResultsView } from '../components/ResultsView';
import { HistoryView } from '../components/HistoryView';
import { Icons } from '../components/ui/Icons';
import { ProcessingModal } from '../components/modals/ProcessingModal';
import { DeleteConfirmModal } from '../components/modals/DeleteConfirmModal';
import { useToast } from '../contexts/ToastContext';

export function Dashboard({ onLogout }) {
  const { showToast } = useToast();
  
  const {
    file, setFile, uploadStep, comparisonData, loadingItem,
    budgets, isLoadingHistory, budgetToDelete, setBudgetToDelete,
    openBudget, handleUpload, handleFindPrice, confirmDelete
  } = useDashboardLogic();

  return (
    <div className="max-w-5xl w-full mx-auto relative z-10">
      <ProcessingModal step={uploadStep} />
      <DeleteConfirmModal isOpen={!!budgetToDelete} onConfirm={confirmDelete} onCancel={() => setBudgetToDelete(null)} />

      <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-10 gap-5 bg-zinc-900/60 p-5 sm:px-8 sm:py-6 rounded-3xl border border-zinc-800 shadow-lg backdrop-blur-xl">
        <div className="flex items-center gap-5">
            <div className="w-14 h-14 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-500/25 border border-white/10">
                <Icons.Hardware className="w-7 h-7 text-white" />
            </div>
            <div>
                <h1 className="text-2xl sm:text-3xl font-black text-zinc-100 tracking-tight">PC Build Analyzer</h1>
                <p className="text-sm font-medium text-zinc-400 mt-0.5">Auditoria Inteligente de Orçamentos</p>
            </div>
        </div>
        <button onClick={onLogout} className="flex items-center text-sm font-bold text-zinc-400 hover:text-red-400 bg-zinc-950 border border-zinc-800 hover:border-red-900/50 transition-all px-5 py-3 rounded-xl hover:bg-red-950/30 w-full sm:w-auto justify-center shadow-sm">
          <Icons.Logout /> Encerrar Sessão
        </button>
      </header>

      <main className="bg-gradient-to-b from-zinc-900/90 to-zinc-950/90 p-6 sm:p-10 rounded-[2rem] border border-zinc-800/80 shadow-2xl backdrop-blur-2xl relative overflow-hidden">
        <div className="absolute -top-[200px] left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-indigo-500/20 blur-[150px] rounded-full pointer-events-none -z-10"></div>
        
        <UploadZone 
          file={file} 
          setFile={setFile} 
          handleUpload={handleUpload} 
          isProcessing={uploadStep > 0} 
          onError={(msg) => showToast(msg, 'error')} 
          statusMsg={{text: '', type: ''}}
        />
        
        <ResultsView 
          data={comparisonData} 
          onFindPrice={handleFindPrice} 
          loadingItem={loadingItem} 
        />
        
        <HistoryView 
          budgets={budgets} 
          isLoading={isLoadingHistory} 
          onOpen={openBudget} 
          onDeleteRequest={setBudgetToDelete} 
        />
      </main>
    </div>
  );
}