import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { ReactReader } from 'react-reader';
import './ReaderView.css';

function ReaderView() {
  const { bookId } = useParams();
  const [location, setLocation] = useState(null);
  const [epubData, setEpubData] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [fileType, setFileType] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchBookData = async () => {
      setIsLoading(true);
      setError('');
      try {
        const response = await fetch(`http://localhost:8001/books/download/${bookId}`);
        if (!response.ok) {
          throw new Error('No se pudo obtener el libro desde el servidor.');
        }
        
        // Detectar el tipo de archivo basándose en el Content-Type
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/pdf')) {
          // Es un PDF - crear URL para el visor
          const blob = await response.blob();
          const url = URL.createObjectURL(blob);
          setPdfUrl(url);
          setFileType('pdf');
        } else if (contentType && contentType.includes('application/epub+zip')) {
          // Es un EPUB - usar ReactReader
          const data = await response.arrayBuffer();
          setEpubData(data);
          setFileType('epub');
        } else {
          // Tipo desconocido - intentar descargar
          const blob = await response.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `libro_${bookId}`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
          setError("Archivo descargado. No se puede previsualizar este tipo de archivo.");
        }
      } catch (err) {
        console.error("Error al obtener los datos del libro:", err);
        setError("No se pudo cargar el libro.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchBookData();

    // Función de limpieza para liberar URLs de objetos
    return () => {
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl);
      }
    };
  }, [bookId]);

  return (
    <div className="reader-container">
      <div className="reader-wrapper">
        {isLoading && <div className="loading-view">Cargando Libro...</div>}
        {error && <div className="loading-view">{error}</div>}
        {!isLoading && !error && fileType === 'pdf' && pdfUrl && (
          <iframe
            src={pdfUrl}
            title="PDF Viewer"
            width="100%"
            height="100%"
            style={{ border: 'none' }}
          />
        )}
        {!isLoading && !error && fileType === 'epub' && epubData && (
          <ReactReader
            url={epubData}
            location={location}
            locationChanged={(epubcfi) => setLocation(epubcfi)}
            epubOptions={{
              flow: "paginated",
              spread: "auto"
            }}
          />
        )}
      </div>
    </div>
  );
}

export default ReaderView;