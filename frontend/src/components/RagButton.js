import React, { useState, useEffect } from 'react';
import { useAppMode } from '../contexts/AppModeContext';
import { getBackendUrl } from '../config/api';
import SimpleChatModal from './SimpleChatModal';
import './RagButton.css';

// Función auxiliar para determinar si un libro puede ser procesado para RAG
const canBookBeProcessedForRag = (book) => {
  // Verificar si el libro tiene archivo local o está en Google Drive
  const hasLocalFile = book.file_path && 
                      (book.file_path.toLowerCase().includes('.pdf') || 
                       book.file_path.toLowerCase().includes('.epub'));
  const hasDriveFile = book.drive_file_id && book.drive_filename && 
                      (book.drive_filename.toLowerCase().includes('.pdf') || 
                       book.drive_filename.toLowerCase().includes('.epub'));
  
  // Para libros locales, también verificar si tienen source: 'local'
  const isLocalBook = book.source === 'local' || (!book.drive_file_id && !book.synced_to_drive);
  
  return hasLocalFile || hasDriveFile || isLocalBook;
};

const RagButton = ({ book, onRagProcessed }) => {
  const [ragStatus, setRagStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isChatModalOpen, setIsChatModalOpen] = useState(false);
  const { appMode } = useAppMode();

  // Verificar estado RAG al montar el componente
  useEffect(() => {
    if (canBookBeProcessedForRag(book)) {
      console.log(`🔍 RAG: Verificando estado del libro ${book.id} (${book.title})`);
      checkRagStatus();
    }
  }, [book.id]);

  const checkRagStatus = async () => {
    setIsLoading(true);
    try {
      const apiUrl = getBackendUrl();
      console.log(`🔍 RAG: Verificando estado en ${apiUrl}/books/${book.id}/rag-status`);
      
      const response = await fetch(`${apiUrl}/books/${book.id}/rag-status`);
      if (response.ok) {
        const status = await response.json();
        console.log(`✅ RAG: Estado obtenido para libro ${book.id}:`, status);
        setRagStatus(status);
      } else {
        console.error('❌ RAG: Error obteniendo estado:', response.statusText);
        // Si el libro no tiene estado RAG, crear uno por defecto
        setRagStatus({
          book_id: book.id,
          rag_processed: false,
          rag_book_id: null,
          rag_chunks_count: null,
          rag_processed_date: null,
          can_process_rag: canBookBeProcessedForRag(book)
        });
      }
    } catch (error) {
      console.error('❌ RAG: Error verificando estado:', error);
      // En caso de error, crear estado por defecto
      setRagStatus({
        book_id: book.id,
        rag_processed: false,
        rag_book_id: null,
        rag_chunks_count: null,
        rag_processed_date: null,
        can_process_rag: canBookBeProcessedForRag(book)
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleProcessRag = async () => {
    setIsProcessing(true);
    try {
      const apiUrl = getBackendUrl();
      console.log(`🔄 RAG: Procesando libro ${book.id} en ${apiUrl}/books/${book.id}/process-rag`);
      
      const response = await fetch(`${apiUrl}/books/${book.id}/process-rag`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const result = await response.json();
        console.log('✅ RAG: Libro procesado exitosamente:', result);
        
        // Actualizar estado local
        await checkRagStatus();
        
        // Notificar al componente padre si es necesario
        if (onRagProcessed) {
          onRagProcessed(book.id, result);
        }
        
        // Mostrar mensaje de éxito
        alert(`✅ ${result.message}`);
      } else {
        const error = await response.json();
        console.error('❌ RAG: Error procesando:', error);
        alert(`❌ Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('❌ RAG: Error de conexión:', error);
      alert('❌ Error de conexión al procesar el libro para RAG');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleOpenRagChat = () => {
    if (ragStatus?.rag_book_id) {
      setIsChatModalOpen(true);
    }
  };

  // Mostrar el botón si el libro puede ser procesado para RAG
  const canProcess = canBookBeProcessedForRag(book);
  
  // Log de depuración para verificar detección de libros
  if (book.drive_file_id) {
    console.log(`🔍 RAG Debug - Libro de Google Drive: ${book.id} (${book.title}):`, {
      file_path: book.file_path,
      drive_file_id: book.drive_file_id,
      drive_filename: book.drive_filename,
      canProcess,
      appMode
    });
  }
  
  if (!canProcess) {
    console.log(`❌ RagButton: Libro ${book.id} (${book.title}) NO puede ser procesado:`, {
      file_path: book.file_path,
      drive_file_id: book.drive_file_id,
      drive_filename: book.drive_filename,
      appMode
    });
    return null;
  }
  
  console.log(`✅ RagButton: Libro ${book.id} (${book.title}) SÍ puede ser procesado:`, {
    file_path: book.file_path,
    drive_file_id: book.drive_file_id,
    drive_filename: book.drive_filename,
    appMode,
    ragStatus: ragStatus?.can_process_rag
  });

  // Determinar el contenido del botón
  let buttonContent = null;

  if (isLoading) {
    buttonContent = (
      <button className="rag-button rag-button--loading" disabled>
        ⏳ Verificando...
      </button>
    );
  } else if (isProcessing) {
    buttonContent = (
      <button className="rag-button rag-button--processing" disabled>
        🔄 Procesando...
      </button>
    );
  } else if (ragStatus?.rag_processed) {
    buttonContent = (
      <div className="rag-button-group">
        <button 
          className="rag-button rag-button--ready" 
          onClick={handleOpenRagChat}
          title={`Chat con IA disponible - ${ragStatus.rag_chunks_count} chunks procesados`}
        >
          🤖 Chat IA
        </button>
        <div className="rag-status-info">
          <span className="rag-chunks-count">{ragStatus.rag_chunks_count} chunks</span>
        </div>
      </div>
    );
  } else {
    // Mostrar botón de procesamiento si el libro puede ser procesado
    const buttonText = appMode === 'drive' ? '🧠 Analizar IA (Nube)' : '🧠 Analizar IA';
    const buttonTitle = appMode === 'drive' 
      ? 'Procesar libro de Google Drive para chat con IA' 
      : 'Procesar libro para chat con IA';
    
    buttonContent = (
      <button 
        className="rag-button rag-button--process" 
        onClick={handleProcessRag}
        title={buttonTitle}
      >
        {buttonText}
      </button>
    );
  }

  return (
    <>
      {buttonContent}
      {/* Modal de chat - Solo un modal por componente */}
      <SimpleChatModal
        isOpen={isChatModalOpen}
        onClose={() => setIsChatModalOpen(false)}
        book={book}
        ragStatus={ragStatus}
      />
    </>
  );
};

export default RagButton;
