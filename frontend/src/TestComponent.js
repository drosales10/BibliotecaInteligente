import React from 'react';

function TestComponent() {
  const testDirectoryPicker = async () => {
    console.log('🧪 TestComponent: Probando showDirectoryPicker...');
    try {
      if (!('showDirectoryPicker' in window)) {
        alert('❌ showDirectoryPicker no está disponible en este navegador');
        return;
      }
      
      console.log('🧪 TestComponent: Llamando a showDirectoryPicker...');
      const dirHandle = await window.showDirectoryPicker();
      console.log('🧪 TestComponent: Carpeta seleccionada:', dirHandle.name);
      alert('✅ TestComponent: Funciona! Carpeta seleccionada: ' + dirHandle.name);
    } catch (error) {
      console.error('🧪 TestComponent: Error en prueba:', error);
      alert('❌ TestComponent: Error: ' + error.message);
    }
  };

  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h2>🧪 Componente de Prueba</h2>
      <p>Este es un componente de prueba independiente para verificar la API showDirectoryPicker</p>
      
      <button 
        onClick={testDirectoryPicker}
        style={{
          padding: '15px 30px',
          backgroundColor: '#2ecc71',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          fontSize: '18px',
          fontWeight: 'bold',
          margin: '20px'
        }}
      >
        🧪 Probar showDirectoryPicker
      </button>
      
      <button 
        onClick={() => {
          console.log('🧪 TestComponent: Botón simple clickeado');
          alert('🧪 TestComponent: Botón simple funciona!');
        }}
        style={{
          padding: '15px 30px',
          backgroundColor: '#e74c3c',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          fontSize: '18px',
          fontWeight: 'bold',
          margin: '20px'
        }}
      >
        🧪 Botón Simple
      </button>
      
      <div style={{ marginTop: '20px', padding: '10px', backgroundColor: '#f8f9fa', borderRadius: '5px' }}>
        <p><strong>Información de Debug:</strong></p>
        <p>showDirectoryPicker disponible: {('showDirectoryPicker' in window) ? '✅ Sí' : '❌ No'}</p>
        <p>User Agent: {navigator.userAgent}</p>
      </div>
    </div>
  );
}

export default TestComponent; 