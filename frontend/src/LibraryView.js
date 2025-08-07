import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, Link, useLocation } from 'react-router-dom';
import { useBookService } from './hooks/useBookService';
import { useAppMode } from './contexts/AppModeContext';
import SyncToDriveButton from './components/SyncToDriveButton';
import BulkSyncToDriveButton from './components/BulkSyncToDriveButton';
import './LibraryView.css';

// Hook personalizado para debounce
const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);
  return debouncedValue;
};

// Componente para la portada (con fallback a genérica)
const BookCover = ({ src, alt, title }) => {
  const [hasError, setHasError] = useState(false);
  useEffect(() => { setHasError(false); }, [src]);
  const handleError = () => { 
    console.error('❌ Error cargando imagen:', src);
    setHasError(true); 
  };

  // Función para obtener la URL correcta de la imagen
  const getImageUrl = (imageSrc) => {
    if (!imageSrc) {
      return '';
    }
    
    // Si es una URL completa (Google Drive), usar el endpoint del backend
    if (imageSrc.startsWith('http') && imageSrc.includes('drive.google.com')) {
      // Extraer el file_id de la URL de Google Drive
      // Formato: https://drive.google.com/file/d/{file_id}/view?usp=drivesdk
      if (imageSrc.includes('/file/d/')) {
        const fileId = imageSrc.split('/file/d/')[1].split('/')[0];
        const backendUrl = `http://localhost:8001/api/drive/cover/${fileId}`;
        return backendUrl;
      }
      
      return imageSrc;
    }
    
    // Si es una ruta local, construir la URL completa
    if (imageSrc.startsWith('/')) {
      return `http://localhost:8001${imageSrc}`;
    }
    
    // Si es solo el nombre del archivo, construir la URL correcta
    // Las imágenes se guardan en static/covers/, pero se sirven desde /static/
    return `http://localhost:8001/static/covers/${imageSrc}`;
  };

  const imageUrl = getImageUrl(src);

  if (hasError || !imageUrl) {
    const initial = title ? title[0].toUpperCase() : '?';
    return (
      <div className="generic-cover">
        <span className="generic-cover-initial">{initial}</span>
      </div>
    );
  }
  
  return <img src={imageUrl} alt={alt} className="book-cover" onError={handleError} />;
};

// Componente para el indicador de ubicación
const LocationIndicator = ({ book }) => {
  const getLocationInfo = () => {
    // Lógica mejorada para determinar la ubicación
    if (book.source === 'drive' || book.drive_file_id) {
      // Si el source es drive o tiene drive_file_id, está en la nube
      return { icon: '☁️', text: 'Cloud', class: 'location-cloud' };
    } else if (book.synced_to_drive === true) {
      // Si está sincronizado, está en la nube
      return { icon: '☁️', text: 'Cloud', class: 'location-cloud' };
    } else {
      // Por defecto, está local
      return { icon: '💾', text: 'Local', class: 'location-local' };
    }
  };

  const locationInfo = getLocationInfo();

  return (
    <div className={`location-indicator ${locationInfo.class}`}>
      <span className="location-icon">{locationInfo.icon}</span>
      <span className="location-text">{locationInfo.text}</span>
    </div>
  );
};

// Modal de confirmación
const DeleteConfirmationModal = ({ isOpen, onClose, onConfirm, bookTitle, isDeleting, isMultiple = false, selectedCount = 0 }) => {
  if (!isOpen) return null;

  // Validar que selectedCount sea un número válido
  const count = typeof selectedCount === 'number' ? selectedCount : 0;
  const title = bookTitle || 'este libro';

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3>Confirmar eliminación</h3>
        {isMultiple ? (
          <p>¿Estás seguro de que quieres eliminar {count} libro{count > 1 ? 's' : ''}?</p>
        ) : (
          <p>¿Estás seguro de que quieres eliminar el libro "{title}"?</p>
        )}
        <p className="warning-text">Esta acción no se puede deshacer.</p>
        <div className="modal-actions">
          <button 
            className="btn-cancel" 
            onClick={onClose}
            disabled={isDeleting}
          >
            Cancelar
          </button>
          <button 
            className="btn-delete" 
            onClick={onConfirm}
            disabled={isDeleting}
          >
            {isDeleting ? 'Eliminando...' : 'Eliminar'}
          </button>
        </div>
      </div>
    </div>
  );
};

function LibraryView() {
  const [searchParams] = useSearchParams();
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearchTerm = useDebounce(searchTerm, 300);
  const [deleteModal, setDeleteModal] = useState({ 
    isOpen: false, 
    bookId: null, 
    bookTitle: '', 
    isMultiple: false, 
    selectedIds: [] 
  });
  const [deletingBookId, setDeletingBookId] = useState(null);
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedBooks, setSelectedBooks] = useState(new Set());
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const location = useLocation();

  // Usar los nuevos hooks
  const { getBooks, deleteBook, appMode } = useBookService();
  const { isLocalMode, isDriveMode } = useAppMode();

  // Función para cargar libros
  const fetchBooks = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const category = searchParams.get('category');
      const booksData = await getBooks(category, debouncedSearchTerm);
      
      // Filtrar libros según el modo actual
      let filteredBooks = booksData;
      
      if (isLocalMode) {
        // En modo local, mostrar solo libros locales (source: 'local' o que no estén en Drive)
        filteredBooks = booksData.filter(book => 
          book.source === 'local' || 
          (!book.synced_to_drive && !book.drive_file_id)
        );
      } else if (isDriveMode) {
        // En modo nube, mostrar solo libros de Drive (source: 'drive' o synced_to_drive: true)
        filteredBooks = booksData.filter(book => 
          book.source === 'drive' || 
          book.synced_to_drive === true ||
          book.drive_file_id
        );
      }
      
      // Agregar información de ubicación a los libros
      const booksWithLocation = filteredBooks.map(book => ({
        ...book,
        // Asegurar que tenga valores por defecto correctos
        source: book.source || (book.drive_file_id ? 'drive' : 'local'),
        synced_to_drive: book.synced_to_drive || false
      }));
      
      setBooks(booksWithLocation);
    } catch (err) {
      console.error('❌ Error en fetchBooks:', err);
      setError(err.message);
      console.error('Error al cargar libros:', err);
    } finally {
      setLoading(false);
    }
  }, [getBooks, searchParams, debouncedSearchTerm, isLocalMode, isDriveMode, appMode]);

  // Efecto para cargar libros al montar el componente
  useEffect(() => {
    fetchBooks();
  }, [fetchBooks]);

  // Efecto para recargar libros cuando cambia el modo de aplicación
  useEffect(() => {
    fetchBooks();
  }, [appMode, isLocalMode, isDriveMode]);

  // Efecto para actualizar libros cuando cambia la ubicación (después de añadir un libro)
  useEffect(() => {
    if (location.state?.refreshBooks) {
      fetchBooks();
      // Limpiar el estado para evitar recargas innecesarias
      window.history.replaceState({}, document.title);
    }
  }, [location.state, fetchBooks]);

  const handleDeleteClick = (bookId, bookTitle) => {
    setDeleteModal({ 
      isOpen: true, 
      bookId, 
      bookTitle: bookTitle || 'Libro sin título', 
      isMultiple: false, 
      selectedIds: [] 
    });
  };

  const handleDeleteConfirm = async () => {
    const { bookId, isMultiple, selectedIds } = deleteModal;
    
    if (isMultiple) {
      await handleBulkDelete(selectedIds);
    } else {
      await handleSingleDelete(bookId);
    }
  };

  const handleSingleDelete = async (bookId) => {
    setDeletingBookId(bookId);
    
    try {
      const response = await deleteBook(bookId);
      
      if (response.ok) {
        // Recargar la lista de libros para actualizar la UI
        fetchBooks();
        resetModal();
      } else {
        const errorData = await response.json();
        alert(`Error al eliminar el libro: ${errorData.detail || 'Error desconocido'}`);
      }
    } catch (err) {
      alert('Error de conexión al intentar eliminar el libro.');
    } finally {
      setDeletingBookId(null);
    }
  };

  const handleBulkDelete = async (bookIds) => {
    try {
      const deletePromises = bookIds.map(async (bookId) => {
        try {
          const response = await deleteBook(bookId);
          return { bookId, response, success: true };
        } catch (error) {
          return { bookId, error: error.message, success: false };
        }
      });
      
      const results = await Promise.all(deletePromises);
      
      const successfulDeletes = results.filter(result => result.success);
      const failedDeletes = results.filter(result => !result.success);

      if (successfulDeletes.length > 0) {
        alert(`Se eliminaron ${successfulDeletes.length} libro${successfulDeletes.length > 1 ? 's' : ''} exitosamente.`);
      }
      if (failedDeletes.length > 0) {
        const errorMessages = failedDeletes.map(result => 
          `Error al eliminar el libro ${result.bookId}: ${result.error}`
        );
        alert(`Error al eliminar algunos libros:\n${errorMessages.join('\n')}`);
      }

      // Re-fetch books to update the UI
      fetchBooks();
      resetModal();
      setSelectionMode(false);
      setSelectedBooks(new Set());
      
    } catch (err) {
      console.error('Error en handleBulkDelete:', err);
      alert('Error de conexión al intentar eliminar los libros.');
    }
  };

  const resetModal = () => {
    setDeleteModal({ 
      isOpen: false, 
      bookId: null, 
      bookTitle: '', 
      isMultiple: false, 
      selectedIds: [] 
    });
  };

  const handleDeleteCancel = () => {
    resetModal();
  };

  const toggleSelectionMode = () => {
    setSelectionMode(!selectionMode);
    if (selectionMode) {
      setSelectedBooks(new Set());
    }
  };

  const toggleBookSelection = (bookId) => {
    const newSelected = new Set(selectedBooks);
    if (newSelected.has(bookId)) {
      newSelected.delete(bookId);
    } else {
      newSelected.add(bookId);
    }
    setSelectedBooks(newSelected);
  };

  const handleBulkDeleteClick = () => {
    if (selectedBooks.size === 0) {
      alert('Selecciona al menos un libro para eliminar.');
      return;
    }
    
    const selectedIdsArray = Array.from(selectedBooks);
    setDeleteModal({
      isOpen: true,
      bookId: null,
      bookTitle: '',
      isMultiple: true,
      selectedIds: selectedIdsArray
    });
  };

  const selectAllBooks = () => {
    if (Array.isArray(books)) {
      setSelectedBooks(new Set(books.map(book => book.id)));
    }
  };

  const deselectAllBooks = () => {
    setSelectedBooks(new Set());
  };

  // Validar que books sea un array antes de renderizar
  const safeBooks = Array.isArray(books) ? books : [];
  const booksLength = safeBooks.length;

  // Función para manejar la sincronización completada
  const handleSyncComplete = useCallback((bookId, result) => {
    // Actualizar el libro en el estado local
    setBooks(prevBooks => 
      prevBooks.map(book => 
        book.id === bookId 
          ? { 
              ...book, 
              synced_to_drive: true, 
              source: 'drive',  // Cambiar a 'drive' ya que ahora está solo en la nube
              file_path: null,  // Limpiar la ruta local
              drive_file_id: result.drive_file_id,
              drive_file_path: result.drive_file_path
            }
          : book
      )
    );
  }, []);

  // Función para manejar la visualización de PDF
  const handleViewPDF = async (book) => {
    try {
      // Primero intentar abrir desde local si existe el archivo
      if (book.file_path && book.source === 'local' && !book.synced_to_drive) {
        // Intentar abrir el PDF local usando el endpoint correcto
        const localUrl = `http://localhost:8001/api/books/download/${book.id}`;
        window.open(localUrl, '_blank');
        return;
      }
      
      // Si está en Drive o sincronizado, intentar desde Drive
      if (book.source === 'drive' || book.synced_to_drive) {
        // Descargar desde Google Drive
        const response = await fetch(`http://localhost:8001/api/drive/books/${book.id}/content`);
        if (response.ok) {
          const result = await response.json();
          if (result.file_path) {
            // Abrir el archivo descargado temporalmente
            window.open(`http://localhost:8001/temp_downloads/${result.file_path}`, '_blank');
          } else {
            alert('No se pudo obtener el archivo desde Google Drive');
          }
        } else {
          alert('Error al obtener el archivo desde Google Drive');
        }
        return;
      }
      
      // Si no está en ninguno de los dos, mostrar mensaje
      alert('El archivo no está disponible localmente ni en Google Drive');
      
    } catch (error) {
      console.error('Error al abrir PDF:', error);
      alert('Error al abrir el archivo PDF');
    }
  };

  return (
    <div className="library-container">
      <div className="library-header">
        <h2>Mi Biblioteca</h2>
        <div className="library-actions">
          <BulkSyncToDriveButton books={safeBooks} onSyncComplete={handleSyncComplete} />
          <button 
            className={`selection-mode-btn ${selectionMode ? 'active' : ''}`}
            onClick={toggleSelectionMode}
          >
            {selectionMode ? 'Cancelar Selección' : 'Seleccionar'}
          </button>
          {selectionMode && (
            <>
              <button className="select-all-btn" onClick={selectAllBooks}>
                Seleccionar Todos
              </button>
              <button className="deselect-all-btn" onClick={deselectAllBooks}>
                Deseleccionar Todos
              </button>
              <button 
                className="bulk-delete-btn"
                onClick={handleBulkDeleteClick}
                disabled={selectedBooks.size === 0}
              >
                Eliminar ({selectedBooks.size})
              </button>
            </>
          )}
        </div>
      </div>
      
      <div className="controls-container">
        <input
          type="text"
          placeholder="Buscar por título, autor o categoría..."
          className="search-bar"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {error && <p className="error-message">{error}</p>}
      {loading && <p>Cargando libros...</p>}
      {!loading && booksLength === 0 && !error && <p>No se encontraron libros que coincidan con tu búsqueda.</p>}

      <div className="book-grid">
        {safeBooks.map((book) => {
          return (
            <div 
              key={book.id} 
              className={`book-card ${book.deleting ? 'deleting' : ''} ${selectedBooks.has(book.id) ? 'selected' : ''}`}
            >
              {selectionMode && (
                <input
                  type="checkbox"
                  className="book-checkbox"
                  checked={selectedBooks.has(book.id)}
                  onChange={() => toggleBookSelection(book.id)}
                />
              )}
              <button 
                onClick={() => handleDeleteClick(book.id, book.title)} 
                className="delete-book-btn" 
                title="Eliminar libro"
                disabled={deletingBookId === book.id || selectionMode}
              >
                {deletingBookId === book.id ? '⋯' : '×'}
              </button>
              <BookCover 
                src={book.cover_image_url || ''}
                alt={`Portada de ${book.title}`}
                title={book.title}
              />
              <div className="book-info">
                <h3 className="book-title">{book.title}</h3>
                <p className="book-author">{book.author}</p>
                <div className="book-category">
                  <span>{book.category}</span>
                </div>
                <LocationIndicator book={book} />
                {book.file_path && book.file_path.toLowerCase().endsWith('.pdf') ? (
                  <button 
                    onClick={() => handleViewPDF(book)}
                    className="view-pdf-btn"
                    title="Ver PDF (prioridad: Local → Cloud)"
                  >
                    📄 Ver PDF
                  </button>
                ) : (
                  <Link to={`/leer/${book.id}`} className="read-link">
                    📖 Leer
                  </Link>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <DeleteConfirmationModal
        isOpen={deleteModal.isOpen}
        onClose={handleDeleteCancel}
        onConfirm={handleDeleteConfirm}
        bookTitle={deleteModal.bookTitle}
        isDeleting={deletingBookId !== null}
        isMultiple={deleteModal.isMultiple}
        selectedCount={deleteModal.selectedIds?.length || 0}
      />
    </div>
  );
}

export default LibraryView;
