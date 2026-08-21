import { useState, useRef, useCallback, useEffect } from 'react';
import { Icons } from './ui/Icons';

export const UploadZone = ({ file, setFile, handleUpload, isProcessing, statusMsg, onError }) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const validateAndSetFile = useCallback((selectedFile) => {
    if (!selectedFile) return;
    
    const validExtensions = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf'];
    if (!validExtensions.includes(selectedFile.type)) {
        onError("Formato inválido. Envie apenas JPG, PNG ou PDF.");
        return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
        onError("Arquivo muito grande. O limite máximo é de 10MB.");
        return;
    }

    setFile(selectedFile);
  }, [onError, setFile]);

  const onDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const onDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (isProcessing) return;
    
    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles?.length > 0) {
        validateAndSetFile(droppedFiles[0]);
    }
  }, [isProcessing, validateAndSetFile]);

  useEffect(() => {
    const handlePaste = (e) => {
      if (isProcessing) return;
      
      const items = e.clipboardData?.items;
      if (!items) return;

      for (const item of items) {
        if (item.type.startsWith('image/')) {
          const pastedFile = item.getAsFile();
          if (!pastedFile) continue;

          const uniqueName = `print_orcamento_${new Date().getTime()}.png`;
          const renamedFile = new File([pastedFile], uniqueName, { type: pastedFile.type });

          const validatedFile = validateAndSetFile(renamedFile);
          
          if (validatedFile) {
             handleUpload(validatedFile); 
          }
          
          e.preventDefault(); 
          break;
        }
      }
    };

    window.addEventListener('paste', handlePaste);
    return () => window.removeEventListener('paste', handlePaste);
  }, [isProcessing, validateAndSetFile, handleUpload]);

  return (
    <div className="space-y-6">
      <div 
        className="flex flex-col items-center justify-center w-full"
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
      >
        <div 
            onClick={() => !isProcessing && fileInputRef.current?.click()}
            className={`flex flex-col items-center justify-center w-full h-56 border-2 border-dashed rounded-xl transition-all duration-200 ease-in-out ${
          file || isDragging 
            ? 'border-indigo-500 bg-indigo-500/5 cursor-default' 
            : 'border-zinc-700 bg-zinc-900/30 hover:bg-zinc-800/50 hover:border-zinc-500 cursor-pointer'
        }`}>
          <div className="flex flex-col items-center justify-center pt-5 pb-6 text-center px-4">
            <Icons.Upload className={`w-10 h-10 mb-4 transition-colors ${isDragging ? 'text-indigo-400' : 'text-zinc-500'}`} />
            
            {isDragging ? (
                <p className="text-base font-semibold text-indigo-400 animate-pulse">Solte o arquivo aqui...</p>
            ) : (
                <>
                    <p className="mb-2 text-sm text-zinc-300">
                        <span className="font-semibold text-indigo-400">Clique para anexar</span> ou arraste e solte o arquivo aqui
                    </p>
                    <p className="text-xs font-medium text-zinc-500 bg-zinc-900 px-3 py-1 rounded-full border border-zinc-800">
                        JPG, PNG ou PDF (Max. 10MB)
                    </p>
                </>
            )}
          </div>
          <input 
            type="file" 
            className="hidden" 
            ref={fileInputRef}
            onChange={(e) => validateAndSetFile(e.target.files[0])} 
            disabled={isProcessing} 
            accept=".jpg,.jpeg,.png,.pdf"
          />
        </div>
      </div>

      {statusMsg.text && (
        <div className={`p-4 rounded-lg text-sm font-medium flex items-center justify-between border shadow-lg ${
          statusMsg.type === 'error' ? 'bg-red-950/80 text-red-400 border-red-900/50' : 
          statusMsg.type === 'success' ? 'bg-emerald-950/80 text-emerald-400 border-emerald-900/50' :
          'bg-indigo-950/50 text-indigo-300 border-indigo-900/50'
        }`}>
          <span>{statusMsg.text}</span>
          {isProcessing && <Icons.Spinner className="h-5 w-5 text-indigo-400" />}
        </div>
      )}

      {file && !isProcessing && statusMsg.type !== 'success' && (
        <div className="flex flex-col sm:flex-row items-center justify-between p-4 bg-zinc-900/80 rounded-xl border border-zinc-700/50 shadow-md gap-4">
          <div className="flex items-center space-x-3 overflow-hidden w-full sm:w-auto">
            <div className="w-10 h-10 shrink-0 rounded-lg bg-zinc-800 flex items-center justify-center text-indigo-400 border border-zinc-700">
              <Icons.Document />
            </div>
            <div className="flex flex-col overflow-hidden">
                <span className="text-sm font-medium text-zinc-200 truncate">{file.name}</span>
                <span className="text-xs text-zinc-500">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
            </div>
          </div>
          <div className="flex gap-2 w-full sm:w-auto">
              <button 
                onClick={() => { setFile(null); onError(""); }}
                className="px-4 py-2 text-sm font-medium text-zinc-400 hover:text-zinc-200 bg-zinc-800/50 hover:bg-zinc-800 rounded-lg transition-colors border border-transparent hover:border-zinc-700 w-full sm:w-auto"
              >
                Cancelar
              </button>
              <button 
                onClick={handleUpload}
                className="px-5 py-2 text-sm font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-500 transition-colors shadow-[0_0_10px_rgba(79,70,229,0.2)] w-full sm:w-auto"
              >
                Processar Orçamento
              </button>
          </div>
        </div>
      )}
    </div>
  );
};