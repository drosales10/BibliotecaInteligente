import React, { useState, useEffect } from 'react';

function TestComponent() {
  const [browserInfo, setBrowserInfo] = useState({});
  const [testResults, setTestResults] = useState([]);

  useEffect(() => {
    // Recopilar información del navegador
    const info = {
      userAgent: navigator.userAgent,
      platform: navigator.platform,
      vendor: navigator.vendor,
      showDirectoryPicker: 'showDirectoryPicker' in window,
      showOpenFilePicker: 'showOpenFilePicker' in window,
      showSaveFilePicker: 'showSaveFilePicker' in window,
      webkitDirectory: 'webkitDirectory' in HTMLInputElement.prototype,
      chrome: navigator.userAgent.includes('Chrome'),
      firefox: navigator.userAgent.includes('Firefox'),
      safari: navigator.userAgent.includes('Safari'),
      edge: navigator.userAgent.includes('Edge'),
      version: getChromeVersion()
    };
    setBrowserInfo(info);
  }, []);

  const getChromeVersion = () => {
    const match = navigator.userAgent.match(/Chrome\/(\d+)/);
    return match ? parseInt(match[1]) : null;
  };

  const addTestResult = (message, type = 'info') => {
    setTestResults(prev => [...prev, { message, type, timestamp: new Date().toLocaleTimeString() }]);
  };

  const testDirectoryPicker = async () => {
    addTestResult('🧪 Iniciando prueba de showDirectoryPicker...', 'info');
    
    try {
      if (!('showDirectoryPicker' in window)) {
        addTestResult('❌ showDirectoryPicker no está disponible en este navegador', 'error');
        return;
      }
      
      addTestResult('✅ showDirectoryPicker está disponible', 'success');
      addTestResult('🔍 Llamando a showDirectoryPicker...', 'info');
      
      const dirHandle = await window.showDirectoryPicker();
      addTestResult(`✅ Carpeta seleccionada: ${dirHandle.name}`, 'success');
      
      // Probar acceso a archivos
      const files = [];
      for await (const entry of dirHandle.values()) {
        if (entry.kind === 'file') {
          const file = await entry.getFile();
          files.push(file.name);
        }
      }
      addTestResult(`📁 Archivos encontrados: ${files.length}`, 'success');
      
    } catch (error) {
      addTestResult(`❌ Error en prueba: ${error.name} - ${error.message}`, 'error');
      console.error('Error completo:', error);
    }
  };

  const testFallbackMethod = () => {
    addTestResult('🧪 Probando método alternativo con input file...', 'info');
    
    try {
      const input = document.createElement('input');
      input.type = 'file';
      input.webkitdirectory = true;
      input.multiple = true;
      
      input.onchange = (event) => {
        const files = Array.from(event.target.files);
        addTestResult(`📁 Método alternativo: ${files.length} archivos encontrados`, 'success');
      };
      
      input.click();
      addTestResult('✅ Método alternativo ejecutado', 'info');
      
    } catch (error) {
      addTestResult(`❌ Error en método alternativo: ${error.message}`, 'error');
    }
  };

  const clearResults = () => {
    setTestResults([]);
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h2>🧪 Diagnóstico de File System Access API</h2>
      
      {/* Información del Navegador */}
      <div style={{ 
        backgroundColor: '#f8f9fa', 
        padding: '20px', 
        borderRadius: '8px', 
        marginBottom: '20px',
        border: '1px solid #dee2e6'
      }}>
        <h3>📊 Información del Navegador</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
          <div><strong>User Agent:</strong> {browserInfo.userAgent}</div>
          <div><strong>Plataforma:</strong> {browserInfo.platform}</div>
          <div><strong>Vendor:</strong> {browserInfo.vendor}</div>
          <div><strong>Versión Chrome:</strong> {browserInfo.version || 'N/A'}</div>
          <div><strong>showDirectoryPicker:</strong> {browserInfo.showDirectoryPicker ? '✅ Sí' : '❌ No'}</div>
          <div><strong>webkitDirectory:</strong> {browserInfo.webkitDirectory ? '✅ Sí' : '❌ No'}</div>
        </div>
      </div>

      {/* Botones de Prueba */}
      <div style={{ marginBottom: '20px' }}>
        <button 
          onClick={testDirectoryPicker}
          style={{
            padding: '15px 30px',
            backgroundColor: '#2ecc71',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: 'bold',
            marginRight: '10px'
          }}
        >
          🧪 Probar showDirectoryPicker
        </button>
        
        <button 
          onClick={testFallbackMethod}
          style={{
            padding: '15px 30px',
            backgroundColor: '#3498db',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: 'bold',
            marginRight: '10px'
          }}
        >
          🔄 Probar Método Alternativo
        </button>
        
        <button 
          onClick={clearResults}
          style={{
            padding: '15px 30px',
            backgroundColor: '#e74c3c',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: 'bold'
          }}
        >
          🗑️ Limpiar Resultados
        </button>
      </div>

      {/* Resultados de las Pruebas */}
      <div style={{ 
        backgroundColor: '#fff', 
        padding: '20px', 
        borderRadius: '8px',
        border: '1px solid #dee2e6',
        maxHeight: '400px',
        overflowY: 'auto'
      }}>
        <h3>📋 Resultados de las Pruebas</h3>
        {testResults.length === 0 ? (
          <p style={{ color: '#6c757d', fontStyle: 'italic' }}>
            Ejecuta una prueba para ver los resultados aquí...
          </p>
        ) : (
          testResults.map((result, index) => (
            <div 
              key={index} 
              style={{ 
                padding: '8px', 
                margin: '5px 0',
                backgroundColor: result.type === 'error' ? '#f8d7da' : 
                               result.type === 'success' ? '#d4edda' : '#d1ecf1',
                border: `1px solid ${result.type === 'error' ? '#f5c6cb' : 
                                   result.type === 'success' ? '#c3e6cb' : '#bee5eb'}`,
                borderRadius: '4px',
                fontSize: '14px'
              }}
            >
              <span style={{ fontWeight: 'bold' }}>[{result.timestamp}]</span> {result.message}
            </div>
          ))
        )}
      </div>

      {/* Recomendaciones */}
      <div style={{ 
        backgroundColor: '#fff3cd', 
        padding: '20px', 
        borderRadius: '8px', 
        marginTop: '20px',
        border: '1px solid #ffeaa7'
      }}>
        <h3>💡 Recomendaciones</h3>
        <ul>
          <li>Si <code>showDirectoryPicker</code> no está disponible, usa el método alternativo</li>
          <li>Verifica que estés usando HTTPS en producción (requerido para File System Access API)</li>
          <li>En desarrollo local, HTTP debería funcionar para Chrome</li>
          <li>Si persiste el problema, verifica la consola del navegador para errores adicionales</li>
        </ul>
      </div>
    </div>
  );
}

export default TestComponent; 