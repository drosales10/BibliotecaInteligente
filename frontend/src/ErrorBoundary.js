import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error capturado por ErrorBoundary:', error, errorInfo);
    this.setState({
      error: error,
      errorInfo: errorInfo
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '20px',
          margin: '20px',
          border: '1px solid #ff6b6b',
          borderRadius: '8px',
          backgroundColor: '#2a2d33',
          color: '#e6e6e6'
        }}>
          <h2 style={{ color: '#ff6b6b', marginTop: 0 }}>Algo salió mal</h2>
          <p>Ha ocurrido un error inesperado en la aplicación.</p>
          <button 
            onClick={() => window.location.reload()} 
            style={{
              padding: '10px 20px',
              backgroundColor: '#61dafb',
              color: '#282c34',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 'bold'
            }}
          >
            Recargar página
          </button>
          {process.env.NODE_ENV === 'development' && this.state.error && (
            <details style={{ marginTop: '20px', whiteSpace: 'pre-wrap' }}>
              <summary style={{ cursor: 'pointer', color: '#61dafb' }}>
                Detalles del error (solo en desarrollo)
              </summary>
              <div style={{ 
                backgroundColor: '#1a1d23', 
                padding: '10px', 
                borderRadius: '4px',
                marginTop: '10px',
                fontSize: '12px'
              }}>
                <strong>Error:</strong> {this.state.error.toString()}
                <br /><br />
                <strong>Stack trace:</strong>
                <pre>{this.state.errorInfo.componentStack}</pre>
              </div>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary; 