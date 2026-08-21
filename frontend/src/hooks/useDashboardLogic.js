import { useState, useCallback, useEffect } from 'react';
import { api } from '../services/api';
import { useToast } from '../contexts/ToastContext';

export function useDashboardLogic() {
  const { showToast } = useToast();
  
  const [file, setFile] = useState(null);
  const [uploadStep, setUploadStep] = useState(0); 
  const [comparisonData, setComparisonData] = useState(null);
  const [loadingItem, setLoadingItem] = useState(null);
  const [budgets, setBudgets] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [budgetToDelete, setBudgetToDelete] = useState(null);

  const loadBudgets = useCallback(async () => {
    const token = localStorage.getItem('token');
    if (!token) return;
    try {
      setIsLoadingHistory(true);
      const data = await api.getBudgets(token);
      setBudgets(data);
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setIsLoadingHistory(false);
    }
  }, [showToast]);

  useEffect(() => { 
    loadBudgets(); 
  }, [loadBudgets]);

  const openBudget = async (budgetId) => {
    const token = localStorage.getItem('token');
    try {
      showToast('Carregando análise...', 'info');
      const compData = await api.getComparison(budgetId, token);
      setComparisonData(compData);
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleUpload = useCallback(async (directFile = null) => {
    const fileToProcess = directFile instanceof File ? directFile : file;
    if (!fileToProcess) return;
    
    setUploadStep(1); 
    setComparisonData(null);

    try {
      const token = localStorage.getItem('token');
      if (!token) throw new Error('Sessão expirada. Faça login novamente.');
      
      const { url_upload, s3_fields, budget_id } = await api.getUploadUrl(fileToProcess.name, token);

      await api.uploadToS3(url_upload, s3_fields, fileToProcess);
      setUploadStep(2);

      await api.processBudget(budget_id, token);
      setUploadStep(3);

      const compData = await api.getComparison(budget_id, token);
      setComparisonData(compData);
      setUploadStep(4); 
      
      await loadBudgets();
      
      setTimeout(() => {
          setUploadStep(0);
          setFile(null);
      }, 1500);

    } catch (err) {
      setUploadStep(0);
      showToast(err.message, 'error');
    }
  }, [file, loadBudgets, showToast]);

  const handleFindPrice = async (itemId) => {
    if (!comparisonData) return;
    setLoadingItem(itemId);
    const token = localStorage.getItem('token');
    const budgetId = comparisonData.budget_id;

    try {
        await api.findPrice(budgetId, itemId, token);
        const MAX_TENTATIVAS = 30;
        const INTERVALO_MS = 2000;

        for (let tentativa = 0; tentativa < MAX_TENTATIVAS; tentativa++) {
            await new Promise(resolve => setTimeout(resolve, INTERVALO_MS));
            const updatedCompData = await api.getComparison(budgetId, token);
            setComparisonData(updatedCompData);
            
            const itemAtualizado = updatedCompData.itens.find((i) => i.item_id === itemId);
            if (itemAtualizado && itemAtualizado.status_scraping !== 'pendente') {
                if (itemAtualizado.status_scraping === 'erro') showToast('Peça não encontrada nas lojas virtuais.', 'error');
                return;
            }
        }
        showToast('O servidor está demorando para responder. Tente novamente mais tarde.', 'error');
    } catch (err) {
        showToast(`Falha no robô: ${err.message}`, 'error');
    } finally {
        setLoadingItem(null);
    }
  };

  const confirmDelete = async () => {
      if (!budgetToDelete) return;
      const idToDelete = budgetToDelete;
      
      setBudgetToDelete(null);
      const previousState = [...budgets];

      setBudgets(prev => prev.filter(b => b.budget_id !== idToDelete));
      
      if (comparisonData?.budget_id === idToDelete) {
          setComparisonData(null);
      }

      try {
          const token = localStorage.getItem('token');
          await api.deleteBudget(idToDelete, token);
          showToast('Orçamento excluído.', 'success');
      } catch (err) {
          setBudgets(previousState);
          showToast(`Não foi possível excluir: ${err.message}`, 'error');
      }
  };

  return {
    file,
    setFile,
    uploadStep,
    comparisonData,
    loadingItem,
    budgets,
    isLoadingHistory,
    budgetToDelete,
    setBudgetToDelete,
    handleUpload,
    handleFindPrice,
    confirmDelete,
    openBudget
  };
}