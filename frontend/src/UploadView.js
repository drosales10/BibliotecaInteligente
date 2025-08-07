import React, { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDriveStatus } from './hooks/useDriveStatus';
import { useBookService } from './hooks/useBookService';
import { useAppMode } from './contexts/AppModeContext';
import './UploadView.css';

function UploadView() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedZip, setSelectedZip] = useState(null);
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [uploadMode, setUploadMode] = useState('single'); // 'single', 'bulk', o 'folder'
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(null);
  const [showHelpModal, setShowHelpModal] = useState(false);
  const navigate = useNavigate();
  const { driveStatus } = useDriveStatus();
  const { uploadBook } = useBookService();
  const { appMode } = useAppMode();

  // Logging para debugging - solo una vez al montar el componente
  useEffect(() => {
    console.log('🔍 UploadView montado con appMode:', appMode);
    console.log('🔍 showDirectoryPicker disponible:', 'showDirectoryPicker' in window);
  }, [appMode]);

  // Logging cuando cambia el modo de upload
  useEffect(() => {
    console.log('🔍 uploadMode cambiado a:', uploadMode);
  }, [uploadMode]);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
    setMessage('');
  };

  const handleZipChange = (event) => {
    setSelectedZip(event.target.files[0]);
    setMessage('');
  };

  const handleFolderSelect = async () => {
    console.log('🔍 handleFolderSelect llamado');
    console.log('🔍 appMode actual:', appMode);
    
    try {
      // Verificar si el navegador soporta la API de directorios
      if (!('showDirectoryPicker' in window)) {
        console.log('❌ showDirectoryPicker no está disponible en este navegador');
        setMessage('❌ Tu navegador no soporta la selección de carpetas. Usa la opción de archivo ZIP.');
        return;
      }

      console.log('🔍 Iniciando selección de carpeta...');
      console.log('🔍 Llamando a window.showDirectoryPicker()...');
      
      const dirHandle = await window.showDirectoryPicker();
      console.log('✅ Carpeta seleccionada:', dirHandle.name);
      
      setSelectedFolder(dirHandle);
      setMessage(`✅ Carpeta seleccionada: ${dirHandle.name}`);
    } catch (error) {
      console.error('❌ Error al seleccionar carpeta:', error);
      if (error.name === 'AbortError') {
        setMessage('❌ Selección de carpeta cancelada por el usuario.');
      } else {
        setMessage('❌ Error al seleccionar la carpeta. Usa la opción de archivo ZIP.');
      }
    }
  };

  const processFolderFiles = async (dirHandle) => {
    const files = [];
    console.log('🔍 Iniciando procesamiento de archivos de carpeta:', dirHandle.name);
    
    const collectFiles = async (handle, depth = 0) => {
      const indent = '  '.repeat(depth);
      console.log(`${indent}📁 Explorando: ${handle.name}`);
      
      try {
        for await (const entry of handle.values()) {
          if (entry.kind === 'file') {
            const file = await entry.getFile();
            console.log(`${indent}📄 Archivo encontrado: ${file.name} (${file.size} bytes)`);
            
            // Solo incluir archivos PDF y EPUB
            if (file.name.toLowerCase().endsWith('.pdf') || 
                file.name.toLowerCase().endsWith('.epub')) {
              files.push(file);
              console.log(`${indent}✅ Archivo válido agregado: ${file.name}`);
            } else {
              console.log(`${indent}❌ Archivo ignorado (no es PDF/EPUB): ${file.name}`);
            }
          } else if (entry.kind === 'directory') {
            console.log(`${indent}📁 Subdirectorio encontrado: ${entry.name}`);
            await collectFiles(entry, depth + 1);
          }
        }
      } catch (error) {
        console.error(`${indent}❌ Error explorando ${handle.name}:`, error);
      }
    };
    
    await collectFiles(dirHandle);
    console.log(`✅ Total de archivos válidos encontrados: ${files.length}`);
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

    // Verificar estado de Google Drive antes de subir
    if (driveStatus.status !== 'ok') {
      setMessage('⚠️ Google Drive no está configurado correctamente. Los libros se almacenarán localmente.');
    }
    
    setIsLoading(true);
    setMessage('Analizando libro con IA... Esto puede tardar un momento.');

    try {
      const result = await uploadBook(selectedFile);
      
      setMessage(`'${result.title}' ha sido añadido exitosamente en modo ${appMode === 'local' ? 'Local' : 'Drive'}. Redirigiendo a la biblioteca...`);
      
      setSelectedFile(null);
      setIsLoading(false);
      
      setTimeout(() => {
        navigate('/', { replace: true });
      }, 1500);
    } catch (error) {
      console.error('Error durante la carga:', error);
      setMessage(`Error: ${error.message || 'No se pudo procesar el archivo.'}`);
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
      // Determinar el endpoint según el modo de la aplicación
      const endpoint = appMode === 'local' 
        ? 'http://localhost:8001/api/upload-bulk-local/'
        : 'http://localhost:8001/upload-bulk/';
      
      setProgress({ current: 0, total: 0, message: `Procesando en modo ${appMode === 'local' ? 'local' : 'nube'}...` });
      
      // Verificar primero si el backend está disponible
      setProgress({ current: 0, total: 0, message: 'Verificando conexión con el servidor...' });
      
      const healthCheck = await fetch('http://localhost:8001/api/drive/status', {
        method: 'GET',
        headers: { 'Origin': 'http://localhost:3000' },
        signal: AbortSignal.timeout(10000) // 10 segundos timeout
      });
      
      if (!healthCheck.ok) {
        throw new Error('El servidor no está respondiendo correctamente');
      }
      
      setProgress({ current: 0, total: 0, message: 'Conexión establecida. Iniciando procesamiento...' });
      
      // Crear un AbortController para manejar timeouts
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 600000); // 10 minutos de timeout
      
      setProgress({ current: 0, total: 0, message: 'Subiendo archivo ZIP al servidor...' });
      
      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
        headers: {
          // No incluir Content-Type, dejar que el navegador lo establezca para FormData
        }
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        
        if (response.status === 503 && appMode !== 'local') {
          throw new Error('Google Drive no está configurado correctamente. Verifica la configuración.');
        } else if (response.status === 413) {
          throw new Error('El archivo ZIP es demasiado grande. Intenta con un archivo más pequeño.');
        } else {
          throw new Error(`Error al procesar el archivo ZIP: ${response.status} ${response.statusText}`);
        }
      }
      
      setProgress({ current: 0, total: 0, message: 'Procesando archivos...' });
      
      const responseData = await response.json();
      
      if (responseData.successful > 0 || responseData.total_files > 0) {
        setProgress({
          current: responseData.successful,
          total: responseData.total_files,
          message: responseData.message
        });
        
        // Crear mensaje detallado con información sobre duplicados y optimización
        let detailedMessage = `✅ ${responseData.message}`;
        if (responseData.duplicates > 0) {
          detailedMessage += `\n\n📋 Resumen:\n`;
          detailedMessage += `• Libros procesados: ${responseData.successful}\n`;
          detailedMessage += `• Errores: ${responseData.failed}\n`;
          detailedMessage += `• Duplicados detectados: ${responseData.duplicates}`;
        }
        
        // Agregar información de optimización si está disponible
        if (responseData.optimization_stats) {
          detailedMessage += `\n\n🚀 Optimización:\n`;
          detailedMessage += `• Llamadas a IA ahorradas: ${responseData.optimization_stats.saved_ai_calls}\n`;
          detailedMessage += `• Archivos únicos procesados: ${responseData.optimization_stats.unique_files}\n`;
          detailedMessage += `• Duplicados detectados previamente: ${responseData.optimization_stats.duplicate_files}`;
        }
        
        setMessage(detailedMessage);
        setSelectedZip(null);
        setIsLoading(false);
        
        setTimeout(() => {
          navigate('/', { replace: true });
        }, 5000); // Más tiempo para leer la información de duplicados
      } else {
        setMessage(`Error: ${responseData.detail || 'No se pudo procesar el archivo ZIP.'}`);
        setIsLoading(false);
        setProgress(null);
      }
    } catch (error) {
      console.error('Error durante la carga masiva:', error);
      
      if (error.name === 'AbortError' || error.name === 'TimeoutError') {
        setMessage('Error: La operación tardó demasiado tiempo. El archivo ZIP puede ser muy grande o el servidor está ocupado. Intenta con un archivo más pequeño.');
      } else if (error.message.includes('Failed to fetch')) {
        setMessage('Error de conexión: No se pudo conectar con el backend. Verifica que el servidor esté ejecutándose en http://localhost:8001');
      } else if (error.message.includes('Google Drive no está configurado') && appMode !== 'local') {
        setMessage('Error: Google Drive no está configurado correctamente. Verifica que el archivo credentials.json esté presente y configurado.');
      } else {
        setMessage(`Error: ${error.message}`);
      }
      
      setIsLoading(false);
      setProgress(null);
    }
  };

  const handleFolderUpload = async () => {
    if (!selectedFolder) {
      setMessage('❌ Por favor, selecciona una carpeta primero.');
      return;
    }

    // Verificar que estamos en modo local
    if (appMode !== 'local') {
      setMessage('❌ La selección de carpeta solo está disponible en modo local. Cambia a modo local para usar esta función.');
      return;
    }
    
    console.log('🚀 Iniciando carga de carpeta en modo local...');
    setIsLoading(true);
    setProgress({ current: 0, total: 0, message: 'Recopilando archivos de la carpeta...' });

    try {
      // Recopilar todos los archivos de la carpeta
      console.log('📁 Recopilando archivos de la carpeta...');
      const files = await processFolderFiles(selectedFolder);
      
      if (files.length === 0) {
        setMessage('❌ No se encontraron archivos PDF o EPUB en la carpeta seleccionada.');
        setIsLoading(false);
        setProgress(null);
        return;
      }

      console.log(`📚 Archivos encontrados: ${files.length}`);
      setProgress({ current: 0, total: files.length, message: `Procesando ${files.length} archivos en modo local...` });

      // Procesar archivos uno por uno (para evitar límites de tamaño)
      let successful = 0;
      let failed = 0;
      let duplicates = 0;

      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        console.log(`📖 Procesando archivo ${i + 1}/${files.length}: ${file.name}`);
        
        setProgress({ 
          current: i + 1, 
          total: files.length, 
          message: `Procesando ${file.name}...` 
        });

        try {
          console.log(`🔄 Enviando ${file.name} al backend...`);
          const response = await uploadBook(file);
          
          if (response && response.success === false && response.isDuplicate) {
            console.log(`⚠️ ${file.name} es un duplicado: ${response.detail}`);
            duplicates++;
          } else if (response && response.id) {
            console.log(`✅ ${file.name} procesado exitosamente`);
            successful++;
          } else {
            console.log(`❌ Error procesando ${file.name}:`, response);
            failed++;
          }
        } catch (error) {
          console.error(`❌ Error procesando ${file.name}:`, error);
          failed++;
        }
      }

      const detailedMessage = `✅ Procesamiento completado.\n\n📋 Resumen:\n• Libros procesados: ${successful}\n• Errores: ${failed}\n• Duplicados detectados: ${duplicates}`;
      
      console.log('🎉 Procesamiento de carpeta completado:', { successful, failed, duplicates });
      setMessage(detailedMessage);
      setSelectedFolder(null);
      setIsLoading(false);
      setProgress(null);
      
      setTimeout(() => {
        navigate('/', { replace: true });
      }, 5000);
    } catch (error) {
      console.error('❌ Error durante el procesamiento de carpeta:', error);
      setMessage('❌ Error de conexión: No se pudo conectar con el backend.');
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

  const openHelpModal = () => {
    setShowHelpModal(true);
  };

  const closeHelpModal = () => {
    setShowHelpModal(false);
  };

  return (
    <div className="upload-view-container" onDrop={handleDrop} onDragOver={handleDragOver}>
            
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
          📚 Carga de Libros en ZIP
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
          <div className="bulk-info">
            <small>Sube un libro (PDF o EPUB) para que la IA lo analice y lo añada a tu biblioteca.</small>
          </div>
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
          <div className="bulk-info">
          <small>
            Sube un archivo ZIP que contenga una carpeta con libros (PDF y EPUB). <br/>
            La aplicación procesará todos los libros de forma concurrente.
          </small>
          
          <div className="help-section">
              
              <button 
                onClick={openHelpModal}
                className="help-button"
                type="button"
                title="Ver instrucciones detalladas"
              >
                ❓ Ayuda
              </button>
            </div></div>
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
        </div>
      ) : (
        <div className="folder-upload-section">
          
          <div className="bulk-info">
          <small>
            Selecciona una carpeta de tu computadora que contenga libros (PDF y EPUB). <br/>
            La aplicación procesará todos los archivos de forma secuencial en modo local.
          </small>
              <button 
                onClick={openHelpModal}
                className="help-button"
                type="button"
                title="Ver instrucciones detalladas"
              >
                ❓ Ayuda
              </button>
            </div>
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
                type="button"
                style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  border: 'none',
                  padding: '12px 24px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '16px',
                  fontWeight: '600',
                  marginTop: '10px',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  zIndex: 1000,
                  position: 'relative'
                }}
              >
                📁 Seleccionar Carpeta
              </button>
            </div>
          </div>
          
          
            
          
        </div>
      )}

      <button 
        onClick={handleUpload} 
        className="upload-button" 
        disabled={isLoading || 
                 (!selectedFile && !selectedZip && !selectedFolder) ||
                 (uploadMode === 'folder' && appMode !== 'local')}
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

      {/* Modal de ayuda */}
      {showHelpModal && (
        <div className="modal-overlay" onClick={closeHelpModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>📋 Instrucciones de Carga</h3>
              <button 
                onClick={closeHelpModal}
                className="modal-close-button"
                type="button"
                title="Cerrar"
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              {uploadMode === 'bulk' ? (
                <div>
                  <h4>📦 Carga Masiva (Archivo ZIP)</h4>
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
              ) : uploadMode === 'folder' ? (
                <div>
                  <h4>📁 Selección de Carpeta (Modo Local)</h4>
                  <ul>
                    <li>Selecciona una carpeta que contenga libros PDF y EPUB</li>
                    <li>La aplicación buscará recursivamente en todos los subdirectorios</li>
                    <li>Se procesarán los archivos uno por uno para evitar límites de tamaño</li>
                    <li>Cada libro será analizado con IA para extraer metadatos</li>
                    <li>Se detectarán automáticamente duplicados por nombre de archivo, título y autor</li>
                    <li>Los duplicados no se agregarán a la biblioteca</li>
                    <li>Los libros se almacenarán localmente en el servidor</li>
                    <li>Esta opción requiere un navegador moderno que soporte la API de directorios</li>
                  </ul>
                </div>
              ) : (
                <div>
                  <h4>📄 Carga Individual</h4>
                  <ul>
                    <li>Selecciona un archivo PDF o EPUB individual</li>
                    <li>El libro será analizado con IA para extraer metadatos</li>
                    <li>Se detectarán automáticamente duplicados por nombre de archivo, título y autor</li>
                    <li>Los duplicados no se agregarán a la biblioteca</li>
                    <li>El libro se almacenará según el modo configurado (local o nube)</li>
                  </ul>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button 
                onClick={closeHelpModal}
                className="modal-ok-button"
                type="button"
              >
                Entendido
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default UploadView;