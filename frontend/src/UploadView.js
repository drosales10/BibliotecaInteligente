import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import './UploadView.css'; // Crearemos este archivo de estilos

function UploadView() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

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
        setMessage(`'${result.title}' ha sido añadido exitosamente. Redirigiendo a la biblioteca...`);
        
        // Limpiar el estado antes de navegar
        setSelectedFile(null);
        setIsLoading(false);
        
        // Usar setTimeout para asegurar que el estado se actualice antes de navegar
        setTimeout(() => {
          // Navegar con replace para evitar problemas de historial
          navigate('/', { replace: true });
        }, 1500);
      } else {
        setMessage(`Error: ${result.detail || 'No se pudo procesar el archivo.'}`);
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Error durante la carga:', error);
      setMessage('Error de conexión: No se pudo conectar con el backend.');
      setIsLoading(false);
    }
  };

  return (
    <div className="upload-view-container" onDrop={handleDrop} onDragOver={handleDragOver}>
      <h2>Añadir Nuevo Libro</h2>
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

export default UploadView;