import React, { useState, useCallback } from 'react';
import LibraryView from './LibraryView'; // Importamos la nueva vista
import './App.css';

function UploadView({ onUploadSuccess }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

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
      setMessage('Por favor, selecciona un archivo primero.');
      return;
    }
    const formData = new FormData();
    formData.append('book_file', selectedFile);
    setIsLoading(true);
    setMessage('Analizando libro con IA... Esto puede tardar un momento.');

    try {
      const response = await fetch('http://localhost:8001/upload-book/', {
        method: 'POST',
        body: formData,
      });
      const result = await response.json();
      if (response.ok) {
        setMessage(`'${result.title}' ha sido añadido a tu biblioteca.`);
        onUploadSuccess(); // Notificar al padre que la subida fue exitosa
      } else {
        // Aquí se mostrará el error de la "puerta de calidad"
        setMessage(`Error: ${result.detail || 'No se pudo procesar el archivo.'}`);
      }
    } catch (error) {
      setMessage(`Error de conexión: No se pudo conectar con el backend.`);
    } finally {
      setIsLoading(false);
      setSelectedFile(null);
    }
  };

  return (
    <div className="upload-view-container" onDrop={handleDrop} onDragOver={handleDragOver}>
      <p>Sube un libro (PDF o EPUB) para que la IA lo analice y lo añada a tu biblioteca.</p>
      <div className="upload-container">
        <div className="drop-zone">
          {selectedFile ? <p>Archivo: {selectedFile.name}</p> : <p>Arrastra y suelta un archivo aquí, o usa el botón</p>}
          <input type="file" id="file-input" onChange={handleFileChange} accept=".pdf,.epub" />
          <label htmlFor="file-input" className="file-label">Seleccionar archivo</label>
        </div>
        <button onClick={handleUpload} className="upload-button" disabled={isLoading}>
          {isLoading ? 'Analizando...' : 'Analizar y Guardar Libro'}
        </button>
        {message && <p className="message">{message}</p>}
      </div>
    </div>
  );
}

function App() {
  const [view, setView] = useState('library'); // Vista por defecto: la biblioteca

  // Esta función se usa para forzar la recarga de la vista de biblioteca
  const [libraryKey, setLibraryKey] = useState(Date.now());

  const handleUploadSuccess = () => {
    // Cambia a la vista de biblioteca y actualiza su 'key' para forzar un re-renderizado
    setView('library');
    setLibraryKey(Date.now());
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Mi Librería Inteligente</h1>
        <nav className="App-nav">
          <button onClick={() => setView('library')} className={view === 'library' ? 'active' : ''}>
            Mi Biblioteca
          </button>
          <button onClick={() => setView('upload')} className={view === 'upload' ? 'active' : ''}>
            Añadir Libro
          </button>
        </nav>
      </header>
      <main className="App-content">
        {view === 'upload' ? (
          <UploadView onUploadSuccess={handleUploadSuccess} />
        ) : (
          <LibraryView key={libraryKey} />
        )}
      </main>
    </div>
  );
}

export default App;
