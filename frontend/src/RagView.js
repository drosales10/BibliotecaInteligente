import React, { useState, useCallback, useEffect } from 'react';
import { getBackendUrl } from './config/api';
import './RagView.css';

function RagView() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [bookId, setBookId] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [currentQuery, setCurrentQuery] = useState('');
  const [ragStats, setRagStats] = useState(null);
  const [libraryRagStats, setLibraryRagStats] = useState(null);
  const [libraryMetrics, setLibraryMetrics] = useState(null);
  const [isCheckingRag, setIsCheckingRag] = useState(false);

  // Verificar estado de RAG al cargar el componente
  useEffect(() => {
    checkRagStatus();
    checkLibraryRagStats();
    checkLibraryMetrics();
  }, []);

  const checkRagStatus = async () => {
    setIsCheckingRag(true);
    try {
      const apiUrl = getBackendUrl();
      const response = await fetch(`${apiUrl}/rag/status`);
      if (response.ok) {
        const result = await response.json();
        setRagStats(result.rag_stats);
        console.log('📊 Estado RAG:', result.rag_stats);
      }
    } catch (error) {
      console.error('❌ Error verificando estado RAG:', error);
    } finally {
      setIsCheckingRag(false);
    }
  };

  const checkLibraryRagStats = async () => {
    try {
      const apiUrl = getBackendUrl();
      const response = await fetch(`${apiUrl}/books/rag-stats`);
      if (response.ok) {
        const result = await response.json();
        setLibraryRagStats(result.library_rag_stats);
        console.log('📚 Estadísticas biblioteca RAG:', result.library_rag_stats);
      }
    } catch (error) {
      console.error('❌ Error verificando estadísticas biblioteca RAG:', error);
    }
  };

  const checkLibraryMetrics = async () => {
    try {
      const apiUrl = getBackendUrl();
      const response = await fetch(`${apiUrl}/api/library/metrics`);
      if (response.ok) {
        const result = await response.json();
        setLibraryMetrics(result.metrics);
        console.log('📊 Métricas de biblioteca:', result.metrics);
      }
    } catch (error) {
      console.error('❌ Error verificando métricas de biblioteca:', error);
    }
  };

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
    setMessage('');
  };

  const handleDrop = useCallback((event) => {
    event.preventDefault();
    event.stopPropagation();
    if (event.dataTransfer.files && event.dataTransfer.files.length > 0) {
      setSelectedFile(event.dataTransfer.files[0]);
      setMessage('');
      event.dataTransfer.clearData();
    }
  }, []);

  const handleDragOver = (event) => {
    event.preventDefault();
    event.stopPropagation();
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setMessage('Por favor, selecciona un archivo PDF o EPUB primero.');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    setIsLoading(true);
    setMessage('Procesando libro para RAG... Esto puede tardar un momento.');

    try {
      const apiUrl = getBackendUrl();
      const response = await fetch(`${apiUrl}/rag/upload-book/`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setBookId(result.book_id);
        
        if (result.status === 'already_exists') {
          setMessage('✅ Este libro ya fue procesado anteriormente. ¡Puedes hacer preguntas!');
        } else {
          setMessage('✅ Libro procesado exitosamente. ¡Ahora puedes hacer preguntas!');
        }
        
        setChatHistory([]); // Clear chat history for new book
        // Actualizar estadísticas
        await checkRagStatus();
        await checkLibraryRagStats();
        await checkLibraryMetrics();
      } else {
        const result = await response.json();
        setMessage(`Error: ${result.detail || 'No se pudo procesar el libro para RAG.'}`);
      }
    } catch (error) {
      setMessage('Error de conexión: No se pudo conectar con el backend.');
    } finally {
      setIsLoading(false);
      setSelectedFile(null);
    }
  };

  const handleQuerySubmit = async (event) => {
    event.preventDefault();
    if (!bookId || !currentQuery.trim()) {
      return;
    }

    const newChatHistory = [...chatHistory, { sender: 'user', text: currentQuery }];
    setChatHistory(newChatHistory);
    setCurrentQuery('');
    setIsLoading(true);

    try {
      const apiUrl = getBackendUrl();
      const response = await fetch(`${apiUrl}/rag/query/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: currentQuery, book_id: bookId }),
      });

      if (response.ok) {
        const result = await response.json();
        setChatHistory([...newChatHistory, { sender: 'gemini', text: result.response }]);
      } else {
        const result = await response.json();
        setChatHistory([...newChatHistory, { sender: 'gemini', text: `Error: ${result.detail || 'No se pudo obtener respuesta.'}` }]);
      }
    } catch (error) {
      setChatHistory([...newChatHistory, { sender: 'gemini', text: 'Error de conexión al consultar.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="rag-view">
      <div className="rag-header">
        <h1>🤖 IA Chat - Conversación con Libros</h1>
        <p>Sube un libro y conversa con él usando inteligencia artificial</p>
      </div>

      {/* Panel de Métricas de la Biblioteca */}
      {libraryMetrics && (
        <div className="rag-stats-panel">
          <h3>📚 Métricas de la Biblioteca</h3>
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-label">Total de Libros:</span>
              <span className="stat-value">{libraryMetrics.total_books}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Libros Locales:</span>
              <span className="stat-value">{libraryMetrics.local_books}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Libros en la Nube:</span>
              <span className="stat-value">{libraryMetrics.cloud_books}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Total de Categorías:</span>
              <span className="stat-value">{libraryMetrics.total_categories}</span>
            </div>
          </div>
          
          {/* Categorías con conteo */}
          {libraryMetrics.categories && libraryMetrics.categories.length > 0 && (
            <div className="categories-breakdown">
              <h4>📖 Distribución por Categorías</h4>
              <div className="categories-grid">
                {libraryMetrics.categories.map((category, index) => (
                  <div key={index} className="category-item">
                    <span className="category-name">{category.name}</span>
                    <span className="category-count">{category.count} libros</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Panel de Estadísticas RAG */}
      <div className="rag-stats-panel">
        <h3>📊 Estado del Sistema RAG</h3>
        {isCheckingRag ? (
          <p>🔄 Verificando estado...</p>
        ) : ragStats ? (
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-label">Total de Embeddings:</span>
              <span className="stat-value">{ragStats.total_embeddings}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Libros Únicos:</span>
              <span className="stat-value">{ragStats.unique_books}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Estado:</span>
              <span className={`stat-status ${ragStats.status === 'active' ? 'active' : 'error'}`}>
                {ragStats.status === 'active' ? '✅ Activo' : '❌ Error'}
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Persistencia:</span>
              <span className="stat-value">✅ Habilitada</span>
            </div>
          </div>
        ) : (
          <p>❌ No se pudo obtener el estado de RAG</p>
        )}
        <button 
          onClick={async () => {
            await checkRagStatus();
            await checkLibraryRagStats();
            await checkLibraryMetrics();
          }} 
          className="refresh-stats-btn"
          disabled={isCheckingRag}
        >
          🔄 Actualizar Estadísticas
        </button>
      </div>

      {/* Panel de Estadísticas de la Biblioteca */}
      {libraryRagStats && (
        <div className="rag-stats-panel">
          <h3>📚 Estado RAG en la Biblioteca</h3>
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-label">Total de Libros:</span>
              <span className="stat-value">{libraryRagStats.total_books}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Disponibles para RAG:</span>
              <span className="stat-value">{libraryRagStats.rag_available}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Procesados con RAG:</span>
              <span className="stat-value">{libraryRagStats.rag_processed}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Pendientes:</span>
              <span className="stat-value">{libraryRagStats.rag_pending}</span>
            </div>
          </div>
          <div className="rag-progress">
            <div className="rag-progress-bar">
              <div 
                className="rag-progress-fill" 
                style={{
                  width: `${libraryRagStats.total_books > 0 
                    ? (libraryRagStats.rag_processed / libraryRagStats.rag_available) * 100 
                    : 0}%`
                }}
              ></div>
            </div>
            <p className="rag-progress-text">
              {libraryRagStats.total_books > 0 
                ? `${Math.round((libraryRagStats.rag_processed / libraryRagStats.rag_available) * 100)}% de libros disponibles procesados`
                : 'Sin libros disponibles'}
            </p>
          </div>
        </div>
      )}

      <div className="rag-content">
        <div className="upload-section">
          <h2>📚 Subir Libro para RAG</h2>
          <div
            className="file-drop-zone"
            onDrop={handleDrop}
            onDragOver={handleDragOver}
          >
            <input
              type="file"
              accept=".pdf,.epub"
              onChange={handleFileChange}
              id="file-input"
              style={{ display: 'none' }}
            />
            <label htmlFor="file-input" className="file-input-label">
              {selectedFile ? (
                <div>
                  <p>📁 Archivo seleccionado: {selectedFile.name}</p>
                  <p>Tamaño: {(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              ) : (
                <div>
                  <p>📁 Arrastra y suelta un archivo PDF o EPUB aquí</p>
                  <p>o haz clic para seleccionar</p>
                </div>
              )}
            </label>
          </div>
          <button
            onClick={handleUpload}
            disabled={!selectedFile || isLoading}
            className="upload-btn"
          >
            {isLoading ? '⏳ Procesando...' : '🚀 Procesar para RAG'}
          </button>
        </div>
        
        {message && (
          <div className={`message ${message.includes('✅') ? 'success' : message.includes('❌') ? 'error' : 'info'}`}>
            {message}
          </div>
        )}
      </div>

      {bookId && (
        <div className="chat-section">
          <h3>Conversación sobre el libro</h3>
          <div className="chat-history">
            {chatHistory.map((msg, index) => (
              <div key={index} className={`chat-message ${msg.sender}`}>
                <strong>{msg.sender === 'user' ? 'Tú' : 'Gemini'}:</strong> {msg.text}
              </div>
            ))}
          </div>
          <form onSubmit={handleQuerySubmit} className="chat-input-form">
            <input
              type="text"
              value={currentQuery}
              onChange={(e) => setCurrentQuery(e.target.value)}
              placeholder="Haz una pregunta sobre el libro..."
              disabled={isLoading}
            />
            <button type="submit" disabled={isLoading || !currentQuery.trim()}>
              Enviar
            </button>
          </form>
        </div>
      )}
    </div>
  );
}

export default RagView;
