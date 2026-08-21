import { Icons } from '../ui/Icons';

export const DeleteConfirmModal = ({ isOpen, onConfirm, onCancel }) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/80 backdrop-blur-sm animate-fade-in px-4">
            <div className="bg-zinc-900 border border-zinc-800 p-6 sm:p-8 rounded-3xl shadow-2xl max-w-sm w-full text-center">
                <div className="w-14 h-14 bg-red-500/10 rounded-full flex items-center justify-center border border-red-500/20 mx-auto mb-5">
                    <Icons.Trash />
                </div>
                <h3 className="text-xl font-bold text-zinc-100 mb-2">Excluir orçamento?</h3>
                <p className="text-sm text-zinc-400 mb-8">Esta ação não poderá ser desfeita. O arquivo e a análise serão perdidos.</p>
                <div className="flex gap-3">
                    <button onClick={onCancel} className="flex-1 px-4 py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-sm font-bold rounded-xl transition-colors">
                        Cancelar
                    </button>
                    <button onClick={onConfirm} className="flex-1 px-4 py-3 bg-red-600 hover:bg-red-500 text-white text-sm font-bold rounded-xl transition-colors shadow-lg shadow-red-900/20">
                        Sim, Excluir
                    </button>
                </div>
            </div>
        </div>
    );
};