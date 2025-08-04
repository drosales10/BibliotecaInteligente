import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, Link, useLocation } from 'react-router-dom';
import { useBooks } from './hooks/useBooks';
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
  const handleError = () => { setHasError(true); };

  if (hasError || !src) {
    const initial = title ? title[0].toUpperCase() : '?';
    return (
      <div className="generic-cover">
        <span className="generic-cover-initial">{initial}</span>
      </div>
    );
  }
  return <img src={src} alt={alt} className="book-cover" onError={handleError} />;
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
  const location = useLocation();

  // Usar el hook personalizado para manejar los libros
  const { books, error, loading, fetchBooks, removeBook, updateBook } = useBooks(searchParams, debouncedSearchTerm);

  // Efecto para cargar libros al montar el componente
  useEffect(() => {
    fetchBooks();
  }, [fetchBooks]);

  // Efecto para actualizar libros cuando cambia la ubicación (después de añadir un libro)
  useEffect(() => {
    // Si venimos de la página de upload, actualizar la lista
    if (location.pathname === '/') {
      fetchBooks();
    }
  }, [location.pathname, fetchBooks]);

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
      const response = await fetch(`http://localhost:8001/books/${bookId}`, { 
        method: 'DELETE' 
      });
      
      if (response.ok) {
        // Animación de eliminación
        updateBook(bookId, { deleting: true });
        
        // Esperar un momento para la animación
        setTimeout(() => {
          removeBook(bookId);
        }, 300);
        
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
      const response = await fetch(`http://localhost:8001/books/bulk`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ book_ids: bookIds })
      });
      
      if (response.ok) {
        const result = await response.json();
        
        // Animación de eliminación para todos los libros seleccionados
        bookIds.forEach(bookId => {
          updateBook(bookId, { deleting: true });
        });
        
        // Esperar un momento para la animación
        setTimeout(() => {
          bookIds.forEach(bookId => {
            removeBook(bookId);
          });
        }, 300);
        
        resetModal();
        setSelectionMode(false);
        setSelectedBooks(new Set());
        
        alert(`Se eliminaron ${result.deleted_count} libro${result.deleted_count > 1 ? 's' : ''} exitosamente.`);
      } else {
        const errorData = await response.json();
        alert(`Error al eliminar los libros: ${errorData.detail || 'Error desconocido'}`);
      }
    } catch (err) {
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

  return (
    <div className="library-container">
      <div className="library-header">
        <h2>Mi Biblioteca</h2>
        <div className="library-actions">
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
        {safeBooks.map((book) => (
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
              src={book.cover_image_url ? `http://localhost:8001/${book.cover_image_url}` : ''}
              alt={`Portada de ${book.title}`}
              title={book.title}
            />
            <div className="book-card-info">
              <h3>{book.title}</h3>
              <p>{book.author}</p>
              <span>{book.category}</span>
            </div>
            {book.file_path && book.file_path.toLowerCase().endsWith('.pdf') ? (
              <a 
                href={`http://localhost:8001/books/download/${book.id}`} 
                className="download-button" 
                target="_blank" 
                rel="noopener noreferrer"
              >
                Leer PDF
              </a>
            ) : (
              <Link to={`/leer/${book.id}`} className="download-button">
                Leer PDF
              </Link>
            )}
          </div>
        ))}
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
