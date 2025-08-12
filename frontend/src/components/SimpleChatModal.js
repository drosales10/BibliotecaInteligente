import React, { useState } from 'react';
import ReactDOM from 'react-dom';
import { getBackendUrl } from '../config/api';

const SimpleChatModal = ({ isOpen, onClose, book, ragStatus }) => {
  const [currentQuery, setCurrentQuery] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!currentQuery.trim() || !ragStatus?.rag_book_id) return;

    const queryText = currentQuery;
    setChatHistory(prev => [...prev, { sender: 'user', text: queryText }]);
    setCurrentQuery('');
    setIsLoading(true);

    try {
      const apiUrl = getBackendUrl();
      console.log(`🤖 RAG: Enviando consulta a ${apiUrl}/rag/query/`);
      
      const response = await fetch(`${apiUrl}/rag/query/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query: queryText, 
          book_id: ragStatus.rag_book_id 
        }),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('✅ RAG: Respuesta recibida:', result);
        setChatHistory(prev => [...prev, { sender: 'ai', text: result.response }]);
      } else {
        const errorData = await response.json();
        console.error('❌ RAG: Error en consulta:', errorData);
        setChatHistory(prev => [...prev, { 
          sender: 'ai', 
          text: `❌ Error: ${errorData.detail || 'Error desconocido en la consulta'}` 
        }]);
      }
    } catch (error) {
      console.error('❌ RAG: Error de conexión:', error);
      setChatHistory(prev => [...prev, { 
        sender: 'ai', 
        text: '❌ Error de conexión. Verifica que el backend esté funcionando.' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const modalContent = (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 99999
    }} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '16px',
        width: '90%',
        maxWidth: '600px',
        maxHeight: '80vh',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.3)'
      }}>
        {/* Header */}
        <div style={{
          padding: '20px',
          borderBottom: '1px solid #e1e5e9',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: '#f8f9fa'
        }}>
          <h3 style={{ margin: 0, color: '#2c3e50' }}>🤖 Chat IA - {book?.title}</h3>
          <button 
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.5rem',
              cursor: 'pointer',
              padding: '8px',
              borderRadius: '50%'
            }}
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '20px', flex: 1, overflow: 'auto' }}>
          {ragStatus?.rag_processed ? (
            <>
              {/* Chat History */}
              <div style={{ 
                maxHeight: '300px', 
                overflowY: 'auto', 
                marginBottom: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px'
              }}>
                {chatHistory.length === 0 ? (
                  <div style={{ textAlign: 'center', color: '#6c757d', padding: '20px' }}>
                    ¡Hola! Hazme cualquier pregunta sobre el libro "{book?.title}".
                    <br />
                    <small style={{ fontSize: '0.9rem', marginTop: '10px', display: 'block' }}>
                      💡 Puedes preguntar sobre el contenido, personajes, temas, etc.
                    </small>
                  </div>
                ) : (
                  chatHistory.map((msg, index) => (
                    <div key={index} style={{
                      padding: '10px',
                      borderRadius: '10px',
                      backgroundColor: msg.sender === 'user' ? '#007bff' : '#f8f9fa',
                      color: msg.sender === 'user' ? 'white' : '#2c3e50',
                      alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                      maxWidth: '80%',
                      wordWrap: 'break-word'
                    }}>
                      {msg.text}
                    </div>
                  ))
                )}
                {isLoading && (
                  <div style={{
                    padding: '10px',
                    borderRadius: '10px',
                    backgroundColor: '#f8f9fa',
                    alignSelf: 'flex-start',
                    maxWidth: '80%'
                  }}>
                    🤖 Escribiendo...
                  </div>
                )}
              </div>

              {/* Input Form */}
              <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '10px' }}>
                <input
                  type="text"
                  value={currentQuery}
                  onChange={(e) => setCurrentQuery(e.target.value)}
                  placeholder="Escribe tu pregunta sobre el libro..."
                  disabled={isLoading}
                  style={{
                    flex: 1,
                    padding: '10px',
                    border: '1px solid #e1e5e9',
                    borderRadius: '20px',
                    outline: 'none'
                  }}
                />
                <button 
                  type="submit"
                  disabled={isLoading || !currentQuery.trim()}
                  style={{
                    background: '#007bff',
                    color: 'white',
                    border: 'none',
                    padding: '10px 20px',
                    borderRadius: '20px',
                    cursor: 'pointer'
                  }}
                >
                  📤
                </button>
              </form>
            </>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <p style={{ fontSize: '1.1rem', marginBottom: '20px' }}>
                📚 Este libro no ha sido procesado para IA aún
              </p>
              <p style={{ color: '#6c757d', marginBottom: '10px' }}>
                Para poder conversar con la IA sobre este libro, primero necesitas procesarlo.
              </p>
              <p style={{ color: '#6c757d' }}>
                {book?.drive_file_id ? 
                  '☁️ El libro se descargará temporalmente desde Google Drive para su análisis.' :
                  '💻 El libro se procesará desde el archivo local.'
                }
              </p>
              <p style={{ 
                background: '#e3f2fd', 
                padding: '15px', 
                borderRadius: '8px', 
                marginTop: '20px',
                fontSize: '0.9rem'
              }}>
                💡 <strong>Tip:</strong> Cierra este modal y usa el botón "🧠 Analizar IA" para procesar el libro.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return ReactDOM.createPortal(modalContent, document.body);
};

export default SimpleChatModal;
