import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import { getBackendUrl } from '../config/api';
import './ChatModal.css';

const ChatModal = ({ isOpen, onClose, book, ragStatus }) => {
  const [chatHistory, setChatHistory] = useState([]);
  const [currentQuery, setCurrentQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  // Log para depuración
  useEffect(() => {
    if (isOpen) {
      console.log('Modal abierto para:', book?.title);
    }
  }, [isOpen, book?.title]);

  // Limpiar historial cuando se abre el modal con un nuevo libro
  useEffect(() => {
    if (isOpen && book) {
      setChatHistory([]);
      setCurrentQuery('');
    }
  }, [isOpen, book]);

  const handleQuerySubmit = async (event) => {
    event.preventDefault();
    if (!ragStatus?.rag_book_id || !currentQuery.trim()) {
      return;
    }

    const queryToSend = currentQuery;
    setChatHistory(prev => [...prev, { sender: 'user', text: queryToSend }]);
    setCurrentQuery('');
    setIsLoading(true);

    try {
      const apiUrl = getBackendUrl();
      const response = await fetch(`${apiUrl}/rag/query/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query: queryToSend, 
          book_id: ragStatus.rag_book_id 
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setChatHistory(prev => [...prev, { sender: 'gemini', text: result.response }]);
      } else {
        const result = await response.json();
        setChatHistory(prev => [...prev, { 
          sender: 'gemini', 
          text: `Error: ${result.detail || 'No se pudo obtener respuesta.'}` 
        }]);
      }
    } catch (error) {
      setChatHistory(prev => [...prev, { 
        sender: 'gemini', 
        text: 'Error de conexión al consultar.' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleProcessRag = async () => {
    if (!book) return;
    
    setIsProcessing(true);
    try {
      const apiUrl = getBackendUrl();
      const response = await fetch(`${apiUrl}/books/${book.id}/process-rag`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Libro procesado para RAG:', result);
        
        // Recargar la página para actualizar el estado del botón
        window.location.reload();
      } else {
        const error = await response.json();
        console.error('Error procesando RAG:', error);
        alert(`❌ Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error de conexión:', error);
      alert('❌ Error de conexión al procesar el libro para RAG');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleModalClick = (e) => {
    e.stopPropagation();
  };

  if (!isOpen) {
    return null;
  }

  const modalContent = (
    <div className="chat-modal-overlay" onClick={handleOverlayClick}>
      <div className="chat-modal" onClick={handleModalClick}>
        <div className="chat-modal-header">
          <h2>🤖 Chat IA - {book?.title}</h2>
          <button className="chat-modal-close" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="chat-modal-body">
          {!ragStatus?.rag_processed ? (
            <div className="rag-not-processed">
              <p>Este libro aún no ha sido procesado para RAG.</p>
              <p>Para poder conversar con la IA, primero debes procesar el libro.</p>
              <button 
                onClick={handleProcessRag}
                disabled={isProcessing}
                className="process-rag-btn"
              >
                {isProcessing ? '🔄 Procesando...' : '🧠 Procesar para RAG'}
              </button>
            </div>
          ) : (
            <>
              <div className="chat-info">
                <p>📚 <strong>{book?.title}</strong> por <strong>{book?.author}</strong></p>
                <p>📊 {ragStatus.rag_chunks_count} chunks procesados</p>
              </div>

              <div className="chat-history">
                {chatHistory.length === 0 ? (
                  <div className="chat-welcome">
                    <p>¡Hola! Soy tu asistente de IA. Puedo ayudarte a entender mejor este libro.</p>
                    <p>Hazme cualquier pregunta sobre el contenido, personajes, temas o conceptos del libro.</p>
                  </div>
                ) : (
                  chatHistory.map((msg, index) => (
                    <div key={index} className={`chat-message ${msg.sender}`}>
                      <div className="message-header">
                        <strong>{msg.sender === 'user' ? 'Tú' : '🤖 IA'}</strong>
                      </div>
                      <div className="message-content">
                        {msg.text}
                      </div>
                    </div>
                  ))
                )}
                {isLoading && (
                  <div className="chat-message gemini">
                    <div className="message-header">
                      <strong>🤖 IA</strong>
                    </div>
                    <div className="message-content">
                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <form onSubmit={handleQuerySubmit} className="chat-input-form">
                <input
                  type="text"
                  value={currentQuery}
                  onChange={(e) => setCurrentQuery(e.target.value)}
                  placeholder="Haz una pregunta sobre el libro..."
                  disabled={isLoading}
                  className="chat-input"
                />
                <button 
                  type="submit" 
                  disabled={isLoading || !currentQuery.trim()}
                  className="chat-send-btn"
                >
                  {isLoading ? '⏳' : '📤'}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );

  // Renderizar el modal usando un portal
  return ReactDOM.createPortal(modalContent, document.body);
};

export default ChatModal;
