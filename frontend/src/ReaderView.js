import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { ReactReader } from 'react-reader';
import { useBookService } from './hooks/useBookService';
import './ReaderView.css';

function ReaderView() {
  const { bookId } = useParams();
  const [location, setLocation] = useState(null);
  const [epubData, setEpubData] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [fileType, setFileType] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const { getBookContent } = useBookService();

  useEffect(() => {
    const fetchBookData = async () => {
      setIsLoading(true);
      setError('');
      try {
        const response = await getBookContent(bookId);
        
        // getBookContent siempre devuelve un blob para archivos locales
        if (response instanceof Blob) {
          const contentType = response.type;
          
          if (contentType && contentType.includes('application/pdf')) {
            // Es un PDF - crear URL para el visor
            const url = URL.createObjectURL(response);
            setPdfUrl(url);
            setFileType('pdf');
          } else if (contentType && contentType.includes('application/epub+zip')) {
            // Es un EPUB - usar ReactReader
            const data = await response.arrayBuffer();
            setEpubData(data);
            setFileType('epub');
          } else {
            // Tipo desconocido - intentar descargar
            const url = URL.createObjectURL(response);
            const a = document.createElement('a');
            a.href = url;
            a.download = `libro_${bookId}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            setError("Archivo descargado. No se puede previsualizar este tipo de archivo.");
          }
        } else {
          // Para libros de Drive, puede devolver JSON
          setError("No se pudo cargar el libro.");
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