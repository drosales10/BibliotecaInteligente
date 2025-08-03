import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import './UploadView.css';

function UploadView() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedZip, setSelectedZip] = useState(null);
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [uploadMode, setUploadMode] = useState('single'); // 'single', 'bulk', o 'folder'
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(null);
  const navigate = useNavigate();

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
    setMessage('');
  };

  const handleZipChange = (event) => {
    setSelectedZip(event.target.files[0]);
    setMessage('');
  };

  const handleFolderSelect = async () => {
    try {
      // Verificar si el navegador soporta la API de directorios
      if (!('showDirectoryPicker' in window)) {
        setMessage('Tu navegador no soporta la selección de carpetas. Usa la opción de archivo ZIP.');
        return;
      }

      const dirHandle = await window.showDirectoryPicker();
      setSelectedFolder(dirHandle);
      setMessage(`Carpeta seleccionada: ${dirHandle.name}`);
    } catch (error) {
      console.error('Error al seleccionar carpeta:', error);
      setMessage('Error al seleccionar la carpeta. Usa la opción de archivo ZIP.');
    }
  };

  const processFolderFiles = async (dirHandle) => {
    const files = [];
    
    const collectFiles = async (handle) => {
      for await (const entry of handle.values()) {
        if (entry.kind === 'file') {
          const file = await entry.getFile();
          if (file.name.toLowerCase().endsWith('.pdf') || 
              file.name.toLowerCase().endsWith('.epub') ||
              file.name.toLowerCase().endsWith('.zip')) {
            files.push(file);
          }
        } else if (entry.kind === 'directory') {
          await collectFiles(entry);
        }
      }
    };
    
    await collectFiles(dirHandle);
    return files;
  };

  const handleDrop = useCallback((event) => {
    event.preventDefault();
    event.stopPropagation();
    if (event.dataTransfer.files && event.dataTransfer.files.length > 0) {
      const file = event.dataTransfer.files[0];
      if (uploadMode === 'single') {
        setSelectedFile(file);
      } else if (uploadMode === 'bulk') {
        setSelectedZip(file);
      }
      setMessage('');
      event.dataTransfer.clearData();
    }
  }, [uploadMode]);

  const handleDragOver = (event) => {
    event.preventDefault();
    event.stopPropagation();
  };

  const handleSingleUpload = async () => {
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
        
        setSelectedFile(null);
        setIsLoading(false);
        
        setTimeout(() => {
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

  const handleBulkUpload = async () => {
    if (!selectedZip) {
      setMessage('Por favor, selecciona un archivo ZIP primero.');
      return;
    }
    
    const formData = new FormData();
    formData.append('folder_zip', selectedZip);
    setIsLoading(true);
    setProgress({ current: 0, total: 0, message: 'Iniciando procesamiento masivo...' });

    try {
      const response = await fetch('http://localhost:8001/upload-bulk/', {
        method: 'POST',
        body: formData,
      });
      
      const result = await response.json();
      
      if (response.ok) {
        setProgress({
          current: result.successful,
          total: result.total_files,
          message: result.message
        });
        
        // Crear mensaje detallado con información sobre duplicados y optimización
        let detailedMessage = `✅ ${result.message}`;
        if (result.duplicates > 0) {
          detailedMessage += `\n\n📋 Resumen:\n`;
          detailedMessage += `• Libros procesados: ${result.successful}\n`;
          detailedMessage += `• Errores: ${result.failed}\n`;
          detailedMessage += `• Duplicados detectados: ${result.duplicates}`;
        }
        
        // Agregar información de optimización si está disponible
        if (result.optimization_stats) {
          detailedMessage += `\n\n🚀 Optimización:\n`;
          detailedMessage += `• Llamadas a IA ahorradas: ${result.optimization_stats.saved_ai_calls}\n`;
          detailedMessage += `• Archivos únicos procesados: ${result.optimization_stats.unique_files}\n`;
          detailedMessage += `• Duplicados detectados previamente: ${result.optimization_stats.duplicate_files}`;
        }
        
        setMessage(detailedMessage);
        setSelectedZip(null);
        setIsLoading(false);
        
        setTimeout(() => {
          navigate('/', { replace: true });
        }, 5000); // Más tiempo para leer la información de duplicados
      } else {
        setMessage(`Error: ${result.detail || 'No se pudo procesar el archivo ZIP.'}`);
        setIsLoading(false);
        setProgress(null);
      }
    } catch (error) {
      console.error('Error durante la carga masiva:', error);
      setMessage('Error de conexión: No se pudo conectar con el backend.');
      setIsLoading(false);
      setProgress(null);
    }
  };

  const handleFolderUpload = async () => {
    if (!selectedFolder) {
      setMessage('Por favor, selecciona una carpeta primero.');
      return;
    }
    
    setIsLoading(true);
    setProgress({ current: 0, total: 0, message: 'Recopilando archivos de la carpeta...' });

    try {
      // Recopilar todos los archivos de la carpeta
      const files = await processFolderFiles(selectedFolder);
      
      if (files.length === 0) {
        setMessage('No se encontraron archivos PDF, EPUB o ZIP en la carpeta seleccionada.');
        setIsLoading(false);
        setProgress(null);
        return;
      }

      setProgress({ current: 0, total: files.length, message: `Procesando ${files.length} archivos...` });

      // Procesar archivos uno por uno (para evitar límites de tamaño)
      let successful = 0;
      let failed = 0;
      let duplicates = 0;

      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        setProgress({ 
          current: i + 1, 
          total: files.length, 
          message: `Procesando ${file.name}...` 
        });

        try {
          const formData = new FormData();
          formData.append('book_file', file);

          const response = await fetch('http://localhost:8001/upload-book/', {
            method: 'POST',
            body: formData,
          });
          
          const result = await response.json();
          
          if (response.ok) {
            successful++;
          } else {
            if (result.detail && result.detail.includes('duplicado')) {
              duplicates++;
            } else {
              failed++;
            }
          }
        } catch (error) {
          console.error(`Error procesando ${file.name}:`, error);
          failed++;
        }
      }

      const detailedMessage = `✅ Procesamiento completado.\n\n📋 Resumen:\n• Libros procesados: ${successful}\n• Errores: ${failed}\n• Duplicados detectados: ${duplicates}`;
      
      setMessage(detailedMessage);
      setSelectedFolder(null);
      setIsLoading(false);
      setProgress(null);
      
      setTimeout(() => {
        navigate('/', { replace: true });
      }, 5000);
    } catch (error) {
      console.error('Error durante el procesamiento de carpeta:', error);
      setMessage('Error de conexión: No se pudo conectar con el backend.');
      setIsLoading(false);
      setProgress(null);
    }
  };

  const handleUpload = () => {
    if (uploadMode === 'single') {
      handleSingleUpload();
    } else if (uploadMode === 'bulk') {
      handleBulkUpload();
    } else if (uploadMode === 'folder') {
      handleFolderUpload();
    }
  };

  return (
    <div className="upload-view-container" onDrop={handleDrop} onDragOver={handleDragOver}>
      <h2>Añadir Libros</h2>
      
      {/* Selector de modo */}
      <div className="upload-mode-selector">
        <button 
          className={`mode-button ${uploadMode === 'single' ? 'active' : ''}`}
          onClick={() => setUploadMode('single')}
        >
          📖 Libro Individual
        </button>
        <button 
          className={`mode-button ${uploadMode === 'bulk' ? 'active' : ''}`}
          onClick={() => setUploadMode('bulk')}
        >
          📚 Carga Masiva
        </button>
        <button 
          className={`mode-button ${uploadMode === 'folder' ? 'active' : ''}`}
          onClick={() => setUploadMode('folder')}
        >
          📁 Seleccionar Carpeta
        </button>
      </div>

      {uploadMode === 'single' ? (
        <div className="single-upload-section">
          <p>Sube un libro (PDF o EPUB) para que la IA lo analice y lo añada a tu biblioteca.</p>
          <div className="upload-container">
            <div className="drop-zone">
              {selectedFile ? (
                <p>Archivo: {selectedFile.name}</p>
              ) : (
                <p>Arrastra y suelta un archivo aquí, o usa el botón</p>
              )}
              <input 
                type="file" 
                id="file-input" 
                onChange={handleFileChange} 
                accept=".pdf,.epub" 
              />
              <label htmlFor="file-input" className="file-label">
                Seleccionar archivo
              </label>
            </div>
          </div>
        </div>
      ) : uploadMode === 'bulk' ? (
        <div className="bulk-upload-section">
          <p>
            Sube un archivo ZIP que contenga una carpeta con libros (PDF y EPUB). 
            La aplicación procesará todos los libros de forma concurrente.
          </p>
          <div className="upload-container">
            <div className="drop-zone">
              {selectedZip ? (
                <p>Archivo ZIP: {selectedZip.name}</p>
              ) : (
                <p>Arrastra y suelta un archivo ZIP aquí, o usa el botón</p>
              )}
              <input 
                type="file" 
                id="zip-input" 
                onChange={handleZipChange} 
                accept=".zip" 
              />
              <label htmlFor="zip-input" className="file-label">
                Seleccionar archivo ZIP
              </label>
            </div>
          </div>
          
          <div className="bulk-info">
            <h4>📋 Instrucciones para carga masiva:</h4>
            <ul>
              <li>Comprime una carpeta que contenga libros PDF y EPUB</li>
              <li>La aplicación buscará recursivamente en todos los subdirectorios</li>
              <li>Se procesarán hasta 4 libros simultáneamente</li>
              <li>Cada libro será analizado con IA para extraer metadatos</li>
              <li>Se detectarán automáticamente duplicados por nombre de archivo, título y autor</li>
              <li>Los duplicados no se agregarán a la biblioteca</li>
              <li>Se procesarán automáticamente archivos ZIP que contengan libros</li>
              <li>Soporte para ZIPs anidados (ZIPs dentro de ZIPs)</li>
            </ul>
          </div>
        </div>
      ) : (
        <div className="folder-upload-section">
          <p>
            Selecciona una carpeta de tu computadora que contenga libros (PDF, EPUB y ZIP). 
            La aplicación procesará todos los archivos de forma secuencial.
          </p>
          <div className="upload-container">
            <div className="drop-zone">
              {selectedFolder ? (
                <p>Carpeta seleccionada: {selectedFolder.name}</p>
              ) : (
                <p>Haz clic en el botón para seleccionar una carpeta</p>
              )}
              <button 
                onClick={handleFolderSelect}
                className="folder-select-button"
              >
                📁 Seleccionar Carpeta
              </button>
            </div>
          </div>
          
          <div className="bulk-info">
            <h4>📋 Instrucciones para selección de carpeta:</h4>
            <ul>
              <li>Selecciona una carpeta que contenga libros PDF, EPUB y ZIP</li>
              <li>La aplicación buscará recursivamente en todos los subdirectorios</li>
              <li>Se procesarán los archivos uno por uno para evitar límites de tamaño</li>
              <li>Cada libro será analizado con IA para extraer metadatos</li>
              <li>Se detectarán automáticamente duplicados por nombre de archivo, título y autor</li>
              <li>Los duplicados no se agregarán a la biblioteca</li>
              <li>Se procesarán automáticamente archivos ZIP que contengan libros</li>
              <li>Esta opción requiere un navegador moderno que soporte la API de directorios</li>
            </ul>
          </div>
        </div>
      )}

      <button 
        onClick={handleUpload} 
        className="upload-button" 
        disabled={isLoading || (!selectedFile && !selectedZip && !selectedFolder)}
      >
        {isLoading ? 'Procesando...' : `Analizar y Guardar ${uploadMode === 'single' ? 'Libro' : 'Libros'}`}
      </button>

      {/* Barra de progreso para carga masiva */}
      {progress && (
        <div className="progress-container">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${(progress.current / progress.total) * 100}%` }}
            ></div>
          </div>
          <p className="progress-text">{progress.message}</p>
        </div>
      )}

      {message && <p className="message">{message}</p>}
    </div>
  );
}

export default UploadView;