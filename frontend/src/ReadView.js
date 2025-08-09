import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAppMode } from './contexts/AppModeContext';
import { getBackendUrl } from './config/api';
import './ReadView.css';

const ReadView = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isLocalMode, isDriveMode } = useAppMode();
  const [book, setBook] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [fileUrl, setFileUrl] = useState(null);

  useEffect(() => {
    const fetchBook = async () => {
      try {
        setLoading(true);
        setError(null);

        // Determinar el endpoint según el modo
        let endpoint;
        if (isLocalMode) {
          endpoint = `${getBackendUrl()}/api/books/`;
        } else if (isDriveMode) {
          endpoint = `${getBackendUrl()}/api/drive/books/`;
        } else {
          // Si no está en ningún modo específico, intentar ambos
          endpoint = `${getBackendUrl()}/api/books/`;
        }

        const response = await fetch(endpoint);
        if (!response.ok) {
          throw new Error('Error al obtener libros');
        }

        const booksData = await response.json();
        
        // Manejar nueva estructura con paginación
        const books = booksData.items || booksData;
        const foundBook = books.find(b => b.id.toString() === id);

        if (!foundBook) {
          // Si no se encuentra en el primer endpoint, intentar el otro
          const altEndpoint = endpoint.includes('drive') 
            ? `${getBackendUrl()}/api/books/`
            : `${getBackendUrl()}/api/drive/books/`;
          
          const altResponse = await fetch(altEndpoint);
          if (!altResponse.ok) {
            throw new Error('Libro no encontrado');
          }

          const altBooksData = await altResponse.json();
          
          // Manejar nueva estructura con paginación
          const altBooks = altBooksData.items || altBooksData;
          const altFoundBook = altBooks.find(b => b.id.toString() === id);

          if (!altFoundBook) {
            throw new Error('Libro no encontrado');
          }

          setBook(altFoundBook);
          
          // Determinar la URL del archivo para el libro alternativo
          if (altFoundBook.file_path && isLocalMode) {
            // Libro local
            setFileUrl(`${getBackendUrl()}/api/books/download/${altFoundBook.id}`);
          } else if (altFoundBook.drive_file_id && isDriveMode) {
            // Libro en Google Drive
            setFileUrl(`${getBackendUrl()}/api/drive/books/${altFoundBook.id}/content`);
          } else {
            // Intentar determinar automáticamente
            if (altFoundBook.file_path) {
              setFileUrl(`${getBackendUrl()}/api/books/download/${altFoundBook.id}`);
            } else if (altFoundBook.drive_file_id) {
              setFileUrl(`${getBackendUrl()}/api/drive/books/${altFoundBook.id}/content`);
            } else {
              throw new Error('No se puede determinar la ubicación del archivo');
            }
          }
        } else {
          setBook(foundBook);
          
          // Determinar la URL del archivo para el libro encontrado
          if (foundBook.file_path && isLocalMode) {
            // Libro local
            setFileUrl(`${getBackendUrl()}/api/books/download/${foundBook.id}`);
            } else if (foundBook.drive_file_id && isDriveMode) {
            // Libro en Google Drive
            setFileUrl(`${getBackendUrl()}/api/drive/books/${foundBook.id}/content`);
          } else {
            // Intentar determinar automáticamente
            if (foundBook.file_path) {
              setFileUrl(`${getBackendUrl()}/api/books/download/${foundBook.id}`);
            } else if (foundBook.drive_file_id) {
              setFileUrl(`${getBackendUrl()}/api/drive/books/${foundBook.id}/content`);
            } else {
              throw new Error('No se puede determinar la ubicación del archivo');
            }
          }
        }

      } catch (err) {
        setError(err.message);
        console.error('Error al cargar libro:', err);
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchBook();
    }
  }, [id, isLocalMode, isDriveMode]);

  const handleBack = () => {
    navigate('/');
  };

  if (loading) {
    return (
      <div className="read-view">
        <div className="read-header">
          <button onClick={handleBack} className="back-button">
            ← Volver a la Biblioteca
          </button>
        </div>
        <div className="loading-container">
          <p>Cargando libro...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="read-view">
        <div className="read-header">
          <button onClick={handleBack} className="back-button">
            ← Volver a la Biblioteca
          </button>
        </div>
        <div className="error-container">
          <h2>Error al cargar el libro</h2>
          <p>{error}</p>
          <button onClick={handleBack} className="back-button">
            Volver a la Biblioteca
          </button>
        </div>
      </div>
    );
  }

  if (!book) {
    return (
      <div className="read-view">
        <div className="read-header">
          <button onClick={handleBack} className="back-button">
            ← Volver a la Biblioteca
          </button>
        </div>
        <div className="error-container">
          <h2>Libro no encontrado</h2>
          <p>El libro con ID {id} no fue encontrado.</p>
          <button onClick={handleBack} className="back-button">
            Volver a la Biblioteca
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="read-view">
      <div className="read-header">
        <button onClick={handleBack} className="back-button">
          ← Volver a la Biblioteca
        </button>
        <div className="book-info-header">
          <h1>{book.title}</h1>
          <p className="author">por {book.author}</p>
          <p className="category">{book.category}</p>
        </div>
      </div>
      
      <div className="reader-container">
        {fileUrl ? (
          <iframe
            src={fileUrl}
            title={`Lector de ${book.title}`}
            className="pdf-viewer"
            width="100%"
            height="100%"
          />
        ) : (
          <div className="no-file-container">
            <h3>Archivo no disponible</h3>
            <p>No se puede acceder al archivo del libro.</p>
            <p>Modo actual: {isLocalMode ? 'Local' : isDriveMode ? 'Nube' : 'Indeterminado'}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReadView; 