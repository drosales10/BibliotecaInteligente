import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams, Link, useLocation } from 'react-router-dom';
import { useBookService } from './hooks/useBookService';
import { useAppMode } from './contexts/AppModeContext';
import { usePagination } from './hooks/usePagination';
import useLoadingState from './hooks/useLoadingState';
import useAdvancedSearch from './hooks/useAdvancedSearch';

import BulkSyncToDriveButton from './components/BulkSyncToDriveButton';
import PaginationControls from './components/PaginationControls';
import LazyImage from './components/LazyImage';


import AdvancedSearchBar from './components/AdvancedSearchBar';
import SearchFilters from './components/SearchFilters';
import FilterChips from './components/FilterChips';
import BookEditModal from './components/BookEditModal';
import RagButton from './components/RagButton';

import { getBackendUrl } from './config/api';
import './LibraryView.css';



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
      const backendUrl = `${getBackendUrl()}/api/drive/cover/${fileId}`;
      return backendUrl;
    }
    
    return imageSrc;
  }
  
  // Si es una ruta local, construir la URL completa
  if (imageSrc.startsWith('/')) {
    return `${getBackendUrl()}${imageSrc}`;
  }
  
  // Si es solo el nombre del archivo, construir la URL correcta
  // Las imágenes se guardan en static/covers/, pero se sirven desde /static/
  return `${getBackendUrl()}/static/covers/${imageSrc}`;
};

// Componente para la portada con lazy loading
const BookCover = ({ src, alt, title }) => {
  const imageUrl = getImageUrl(src);
  const initial = title ? title[0].toUpperCase() : '?';
  
  // Fallback personalizado para libros
  const fallbackElement = (
    <div className="generic-cover">
      <span className="generic-cover-initial">{initial}</span>
    </div>
  );

  return (
    <LazyImage
      src={imageUrl}
      alt={alt}
      title={title}
      className="book-cover-lazy"
      variant="book-cover"
      showSkeleton={true}
      skeletonProps={{
        variant: 'book-cover',
        width: '100%',
        height: '280px'
      }}
      fallback={fallbackElement}
      threshold={0.1}
      rootMargin="100px"
    />
  );
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
  const [deleteModal, setDeleteModal] = useState({ 
    isOpen: false, 
    bookId: null, 
    bookTitle: '', 
    isMultiple: false, 
    selectedIds: [] 
  });
  
  // Log del estado del modal para depuración
      // Estado actual del deleteModal
  const [deletingBookId, setDeletingBookId] = useState(null);
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedBooks, setSelectedBooks] = useState(new Set());
  const [books, setBooks] = useState([]);
  const [error, setError] = useState(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [editModal, setEditModal] = useState({ 
    isOpen: false, 
    book: null 
  });
  const [categories, setCategories] = useState([]);
  const location = useLocation();

  // Usar los nuevos hooks
  const { getBooks, deleteBook, getCategories } = useBookService();
  const { appMode, isLocalMode, isDriveMode } = useAppMode();
  
  // Hook de búsqueda avanzada
  const {
    searchTerm,
    filters,
    suggestions,
    searchHistory,
    isAdvancedMode,
    isLoading: searchLoading,
    updateSearchTerm,
    updateFilters,
    clearSearch,
    toggleAdvancedMode,
    removeFilter,
    clearAllFilters,
    getActiveFilters,
    performSearch: debouncedSearch,
    searchImmediately
  } = useAdvancedSearch();
  
  // Hook de paginación
  const {
    currentPage,
    perPage,
    totalItems,
    totalPages,
    paginationInfo,
    goToPage,
    changePerPage,
    updatePaginationInfo,
    resetPagination
  } = usePagination(1, 20);

  // Hook de estados de carga mejorados
  const {
    isLoading,
    withLoading
  } = useLoadingState({
    initial: true,
    search: false,
    pagination: false,
    delete: false,
    bulkDelete: false,
    sync: false
  });

  // Función de búsqueda optimizada para el hook avanzado
  const handleAdvancedSearch = useCallback(async (searchParams) => {
    try {
      const { term = '', filters: searchFilters = {}, category = null } = searchParams;
      
      const booksData = await getBooks(category, term, currentPage, perPage);
      
      if (booksData && booksData.items) {
        const { items: booksList, pagination } = booksData;
        
        // Aplicar filtros adicionales si existen
        let filteredBooks = booksList;
        
        if (searchFilters.author) {
          filteredBooks = filteredBooks.filter(book => 
            book.author && book.author.toLowerCase().includes(searchFilters.author.toLowerCase())
          );
        }
        
        if (searchFilters.category && searchFilters.category !== category) {
          filteredBooks = filteredBooks.filter(book => 
            book.category && book.category.toLowerCase() === searchFilters.category.toLowerCase()
          );
        }
        
        if (searchFilters.fileType) {
          filteredBooks = filteredBooks.filter(book => 
            book.file_path && book.file_path.toLowerCase().endsWith(searchFilters.fileType.toLowerCase())
          );
        }
        
        if (searchFilters.source) {
          filteredBooks = filteredBooks.filter(book => book.source === searchFilters.source);
        }
        
        if (searchFilters.hasCover) {
          filteredBooks = filteredBooks.filter(book => book.cover_image);
        }
        
        if (searchFilters.hasFile) {
          filteredBooks = filteredBooks.filter(book => book.file_path);
        }
        
        // Filtrar por modo actual
        if (isLocalMode) {
          filteredBooks = filteredBooks.filter(book => 
            book.source === 'local' || 
            (!book.synced_to_drive && !book.drive_file_id)
          );
        } else if (isDriveMode) {
          filteredBooks = filteredBooks.filter(book => 
            book.source === 'drive' || 
            book.synced_to_drive === true ||
            book.drive_file_id
          );
        }
        
        // Actualizar estado de libros
        setBooks(filteredBooks);
        
        // Actualizar información de paginación
        if (pagination) {
          updatePaginationInfo({
            total: filteredBooks.length,
            page: pagination.current_page || 1,
            per_page: pagination.per_page || perPage,
            pages: Math.ceil(filteredBooks.length / (pagination.per_page || perPage))
          });
        }
        
        return filteredBooks;
      }
      
      setBooks([]);
      return [];
    } catch (error) {
      console.error('Error en búsqueda avanzada:', error);
      setError('Error al realizar la búsqueda');
      throw error;
    }
  }, [getBooks, currentPage, perPage, isLocalMode, isDriveMode, updatePaginationInfo, setBooks, setError]);

  // Función para cargar libros
  const fetchBooks = useCallback(async () => {
    try {
      setError(null);
      
      const category = searchParams.get('category');
      // Usar el término de búsqueda del hook avanzado
      const searchQuery = searchTerm;
      
      console.log('🚀 fetchBooks iniciado:', {
        mode: isLocalMode ? 'LOCAL' : (isDriveMode ? 'DRIVE' : 'OTRO'),
        category,
        searchQuery,
        currentPage,
        perPage
      });
      
      const booksData = await getBooks(category, searchQuery, currentPage, perPage);
      
      console.log('📊 Respuesta del backend:', {
        hasData: !!booksData,
        hasItems: !!(booksData && booksData.items),
        itemsCount: booksData?.items?.length || 0,
        hasPagination: !!(booksData && booksData.pagination),
        rawData: booksData
      });
      
      // Verificar si la respuesta tiene estructura de paginación
      if (booksData && booksData.items && booksData.pagination) {
        // Nueva estructura con paginación
        const { items: booksList, pagination } = booksData;
        
        // Filtrar libros según el modo actual
        let filteredBooks = booksList;
        console.log('📚 Total de libros recibidos:', booksList.length);
        console.log('🔧 Modo actual:', isLocalMode ? 'LOCAL' : (isDriveMode ? 'DRIVE' : 'OTRO'));
        
        if (isLocalMode) {
          // En modo local, mostrar solo libros locales (source: 'local' o que no estén en Drive)
          const beforeFilter = booksList.length;
          filteredBooks = booksList.filter(book => 
            book.source === 'local' || 
            (!book.synced_to_drive && !book.drive_file_id)
          );
          console.log('🔍 Filtrado local: de', beforeFilter, 'a', filteredBooks.length, 'libros');
          if (filteredBooks.length === 0 && booksList.length > 0) {
            console.log('⚠️ Primer libro para debug:', booksList[0]);
          }
        } else if (isDriveMode) {
          // En modo nube, mostrar solo libros de Drive
          // Priorizar drive_file_id que es el campo más confiable del backend
          const beforeFilter = booksList.length;
          filteredBooks = booksList.filter(book => {
            // Si tiene drive_file_id, definitivamente está en Drive
            if (book.drive_file_id) {
              return true;
            }
            // Si tiene source: 'drive', está en Drive
            if (book.source === 'drive') {
              return true;
            }
            // Si está marcado como sincronizado, está en Drive
            if (book.synced_to_drive === true) {
              return true;
            }
            return false;
          });
          console.log('🔍 Filtrado drive: de', beforeFilter, 'a', filteredBooks.length, 'libros');
          if (filteredBooks.length === 0 && booksList.length > 0) {
            console.log('⚠️ Primer libro para debug (modo drive):', booksList[0]);
            console.log('🔍 Campos del primer libro:', {
              source: booksList[0].source,
              synced_to_drive: booksList[0].synced_to_drive,
              drive_file_id: booksList[0].drive_file_id
            });
          }
        }
        
        // Agregar información de ubicación a los libros
        const booksWithLocation = filteredBooks.map(book => ({
          ...book,
          // Asegurar que tenga valores por defecto correctos
          source: book.source || (book.drive_file_id ? 'drive' : 'local'),
          synced_to_drive: book.synced_to_drive || false
        }));
        
        console.log('📖 Libros finales para setBooks:', booksWithLocation.length);
        console.log('📝 Primer libro final:', booksWithLocation[0]);
        console.log('🔍 Resumen del filtrado:', {
          totalRecibidos: booksList.length,
          totalFiltrados: filteredBooks.length,
          totalFinal: booksWithLocation.length,
          modo: isLocalMode ? 'LOCAL' : (isDriveMode ? 'DRIVE' : 'OTRO')
        });
        setBooks(booksWithLocation);

        updatePaginationInfo(pagination);
      } else {
        // Estructura antigua (sin paginación) - mantener compatibilidad
        let filteredBooks = booksData;
        
        if (isLocalMode) {
          filteredBooks = booksData.filter(book => 
            book.source === 'local' || 
            (!book.synced_to_drive && !book.drive_file_id)
          );
        } else if (isDriveMode) {
          filteredBooks = booksData.filter(book => {
            // Si tiene drive_file_id, definitivamente está en Drive
            if (book.drive_file_id) {
              return true;
            }
            // Si tiene source: 'drive', está en Drive
            if (book.source === 'drive') {
              return true;
            }
            // Si está marcado como sincronizado, está en Drive
            if (book.synced_to_drive === true) {
              return true;
            }
            return false;
          });
        }
        
        const booksWithLocation = filteredBooks.map(book => ({
          ...book,
          source: book.source || (book.drive_file_id ? 'drive' : 'local'),
          synced_to_drive: book.synced_to_drive || false
        }));
        
        console.log('📖 Libros finales (estructura antigua):', booksWithLocation.length);
        console.log('🔍 Resumen del filtrado (estructura antigua):', {
          totalRecibidos: booksData.length,
          totalFiltrados: filteredBooks.length,
          totalFinal: booksWithLocation.length,
          modo: isLocalMode ? 'LOCAL' : (isDriveMode ? 'DRIVE' : 'OTRO')
        });
        
        setBooks(booksWithLocation);

        updatePaginationInfo({ total: booksData.length, page: 1, per_page: booksData.length });
      }
    } catch (error) {
      console.error('Error al cargar libros:', error);
      setError('Error al cargar los libros. Por favor, inténtalo de nuevo.');
    } finally {
      console.log('🏁 fetchBooks terminado');
      console.log('🔍 Estado final después de fetchBooks:', {
        books: books.length,
        error,
        modo: isLocalMode ? 'LOCAL' : (isDriveMode ? 'DRIVE' : 'OTRO')
      });
    }
  }, [getBooks, searchParams, searchTerm, currentPage, perPage, isLocalMode, isDriveMode, updatePaginationInfo]); // Dependencias completas



  // Función para actualizar libros manualmente
  const refreshBooks = useCallback(() => {
    console.log('🔄 refreshBooks llamado manualmente');
    fetchBooks();
  }, [fetchBooks]);

  // Efecto para cargar libros al montar el componente (solo una vez)
  useEffect(() => {
    if (!isInitialized) {
      const loadBooks = async () => {
        try {
          console.log('🚀 Iniciando carga inicial de libros...');
          await fetchBooks(); // Usar fetchBooks directamente
          console.log('✅ Carga inicial completada');
          setIsInitialized(true);
        } catch (error) {
          console.error('❌ Error al cargar libros iniciales:', error);
          setIsInitialized(true); // Marcar como inicializado incluso si hay error
        }
      };
      loadBooks();
    }
  }, [isInitialized, fetchBooks]); // Incluir fetchBooks en las dependencias

  // Efecto para recargar libros cuando cambia el modo de aplicación
  useEffect(() => {
    console.log('🔄 useEffect appMode detectado:', {
      appMode,
      isInitialized,
      isLocalMode,
      isDriveMode
    });
    
    // Solo recargar si ya se han inicializado
    if (isInitialized) {
      console.log('🔄 Recargando libros por cambio de modo...');
      console.log('🔍 Estado actual antes de fetchBooks:', {
        books: books.length,
        error,
        loading: isLoading('initial')
      });
      // Usar fetchBooks directamente en lugar de withLoading para evitar duplicados
      fetchBooks();
    } else {
      console.log('⏳ No se recargan libros - componente no inicializado');
    }
  }, [appMode, isInitialized, fetchBooks]); // Incluir fetchBooks en las dependencias

  // Efecto para actualizar libros cuando cambia la ubicación (después de añadir un libro)
  useEffect(() => {
    if (location.state?.refreshBooks) {
      console.log('🔄 Recargando libros por cambio de ubicación...');
      // Usar fetchBooks directamente en lugar de withLoading para evitar duplicados
      fetchBooks();
      // Limpiar el estado para evitar recargas innecesarias
      window.history.replaceState({}, document.title);
    }
  }, [location.state, fetchBooks]); // Incluir fetchBooks en las dependencias

  // Los efectos de sincronización ya no son necesarios con el nuevo sistema unificado

  // Efecto para resetear paginación cuando cambia la búsqueda
  useEffect(() => {
    if (searchTerm.trim() || Object.values(filters).some(v => v && v !== '')) {
      resetPagination();
    }
  }, [searchTerm, filters, resetPagination]);

  // Efecto para recargar libros cuando cambia la paginación (solo si no hay búsqueda activa)
  useEffect(() => {
    if (!searchTerm.trim() && !Object.values(filters).some(v => v && v !== '') && isInitialized) {
      console.log('🔄 Cambio en paginación detectado, recargando libros...');
      // Usar fetchBooks directamente en lugar de withLoading para evitar duplicados
      fetchBooks();
    }
  }, [currentPage, perPage, isInitialized, searchTerm, filters, fetchBooks]); // Incluir fetchBooks en las dependencias

  const handleDeleteClick = (bookId, bookTitle) => {
    // handleDeleteClick llamado
    setDeleteModal({ 
      isOpen: true, 
      bookId, 
      bookTitle: bookTitle || 'Libro sin título', 
      isMultiple: false, 
      selectedIds: [] 
    });
    // Modal configurado para abrirse
  };

  const handleDeleteConfirm = async () => {
    // handleDeleteConfirm llamado
    const { bookId, isMultiple, selectedIds } = deleteModal;
    
    if (isMultiple) {
              // Ejecutando eliminación masiva
      await handleBulkDelete(selectedIds);
    } else {
              // Ejecutando eliminación individual
      await handleSingleDelete(bookId);
    }
  };

  const handleSingleDelete = async (bookId) => {
    // handleSingleDelete iniciado
    setDeletingBookId(bookId);
    
    try {
      // Llamando a deleteBook
      const response = await deleteBook(bookId);
      // Respuesta de deleteBook recibida
      
      if (response.ok) {
        // Eliminación exitosa, recargando libros
        // Recargar la lista de libros para actualizar la UI
        console.log('🔄 Recargando libros después de eliminación...');
        await fetchBooks(); // Usar fetchBooks directamente
        resetModal();
      } else {
        // Error en respuesta del servidor
        const errorData = await response.json();
        alert(`Error al eliminar el libro: ${errorData.detail || 'Error desconocido'}`);
      }
    } catch (err) {
      console.error('🔍 Error en handleSingleDelete:', err);
      alert('Error de conexión al intentar eliminar el libro.');
    } finally {
      setDeletingBookId(null);
    }
  };

  const handleBulkDelete = async (bookIds) => {
    try {
      // handleBulkDelete iniciado
      
      if (isDriveMode) {
        // En modo nube, usar el endpoint de eliminación masiva de Drive
                  // Usando eliminación masiva de Drive
        const response = await fetch(`${getBackendUrl()}/api/drive/books/bulk`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ book_ids: bookIds }),
        });
        
        if (response.ok) {
          const result = await response.json();
          // Resultado de eliminación masiva recibido
          
          if (result.deleted_count > 0) {
            alert(`Se eliminaron ${result.deleted_count} libro${result.deleted_count > 1 ? 's' : ''} exitosamente.`);
          }
          if (result.failed_count > 0) {
            const errorMessages = result.failed_deletions.join('\n');
            alert(`Error al eliminar algunos libros:\n${errorMessages}`);
          }
        } else {
          const errorData = await response.json();
          alert(`Error al eliminar libros: ${errorData.detail || 'Error desconocido'}`);
        }
      } else {
        // En modo local, usar eliminación individual
                  // Usando eliminación individual para modo local
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
      }

      // Re-fetch books to update the UI
      console.log('🔄 Recargando libros después de eliminación masiva...');
      await fetchBooks(); // Usar fetchBooks directamente
      resetModal();
      setSelectionMode(false);
      setSelectedBooks(new Set());
      
    } catch (err) {
      console.error('🔍 Error en handleBulkDelete:', err);
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
  
  // Debug del estado de renderizado
  console.log('🎨 Renderizando LibraryView:');
  console.log('   📚 books state:', books);
  console.log('   📚 safeBooks length:', booksLength);
  console.log('   🔄 isLoading(initial):', isLoading('initial'));
  console.log('   🔍 isLoading(search):', isLoading('search'));
  console.log('   📄 isLoading(pagination):', isLoading('pagination'));
  console.log('   ✅ isInitialized:', isInitialized);
  


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
      // Verificar si el libro está en modo local o nube
      if (book.source === 'local' || (!book.synced_to_drive && !book.drive_file_id)) {
        // Libro local - abrir en nueva pestaña
        const url = `${getBackendUrl()}/api/books/download/${book.id}`;
        window.open(url, '_blank');
        return;
      } else if (book.source === 'drive' || book.synced_to_drive || book.drive_file_id) {
        // Libro en Google Drive - abrir en nueva pestaña
        const url = `${getBackendUrl()}/api/drive/books/${book.id}/content`;
        window.open(url, '_blank');
        return;
      }
      
      // Si no está en ninguno de los dos, mostrar mensaje
      alert('El archivo no está disponible localmente ni en Google Drive');
      
    } catch (error) {
      console.error('Error al abrir PDF:', error);
      alert('Error al abrir el archivo PDF');
    }
  };

  const handleEditBook = (book) => {
    setEditModal({ isOpen: true, book });
  };

  const handleCloseEditModal = () => {
    setEditModal({ isOpen: false, book: null });
  };

  const handleBookUpdate = (updatedBook) => {
    setBooks(prevBooks => 
      prevBooks.map(book => 
        book.id === updatedBook.id ? updatedBook : book
      )
    );
  };

  const handleCategoryCreate = (newCategory) => {
    setCategories(prev => [...prev, newCategory]);
  };

  const handleSearchCoverOnline = async (book) => {
    try {
      console.log('Buscando portada online para:', book.title);
      
      const response = await fetch(`${getBackendUrl()}/api/books/${book.id}/search-cover-online`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (response.ok && data.success) {
        console.log('Portada encontrada:', data.cover_url);
        // Actualizar la lista de libros para reflejar el cambio
        refreshBooks();
        alert(`✅ Portada encontrada y actualizada: ${data.cover_url}`);
      } else {
        console.error('Error al buscar portada:', data.message);
        alert(`❌ No se pudo encontrar portada online: ${data.message}`);
      }
    } catch (error) {
      console.error('Error al buscar portada online:', error);
      alert('❌ Error al buscar portada online. Verifica la conexión.');
    }
  };

  const handleBulkSearchCovers = async () => {
    try {
      console.log('Iniciando búsqueda masiva de portadas para', safeBooks.length, 'libros');
      
      // Obtener IDs de libros que no tienen portada o tienen portadas genéricas
      const booksWithoutCovers = safeBooks.filter(book => 
        !book.cover_image_url || 
        book.cover_image_url.includes('generic') ||
        book.cover_image_url.includes('placeholder')
      );
      
      if (booksWithoutCovers.length === 0) {
        alert('✅ Todos los libros ya tienen portadas. No es necesario buscar nuevas portadas.');
        return;
      }
      
      const bookIds = booksWithoutCovers.map(book => book.id);
      
      const response = await fetch(`${getBackendUrl()}/api/books/bulk-search-covers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(bookIds),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        console.log('Búsqueda masiva completada:', data);
        // Actualizar la lista de libros para reflejar los cambios
        refreshBooks();
        alert(`✅ Búsqueda masiva completada:\n${data.successful} portadas encontradas\n${data.failed} no encontradas`);
      } else {
        console.error('Error en búsqueda masiva:', data.message);
        alert(`❌ Error en búsqueda masiva: ${data.message}`);
      }
    } catch (error) {
      console.error('Error al realizar búsqueda masiva:', error);
      alert('❌ Error al realizar búsqueda masiva. Verifica la conexión.');
    }
  };

  const fetchCategories = useCallback(async () => {
    try {
      const cats = await getCategories();
      setCategories(cats);
    } catch (error) {
      console.error('Error cargando categorías:', error);
    }
  }, [getCategories]);

  // Cargar categorías al montar el componente
  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  return (
    <div className="library-container">
      <div className="library-header">
        
        <div className="library-actions">
          <BulkSyncToDriveButton books={safeBooks} onSyncComplete={handleSyncComplete} />
          <button 
            className="bulk-search-covers-btn"
            onClick={handleBulkSearchCovers}
            disabled={safeBooks.length === 0}
            title="Buscar portadas online para todos los libros"
          >
            🔍 Buscar Portadas
          </button>
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
        <AdvancedSearchBar
          searchTerm={searchTerm}
          onSearchChange={(term) => {
            updateSearchTerm(term);
            // Ejecutar búsqueda avanzada con debounce
            if (term.trim()) {
              debouncedSearch({ term, filters }, handleAdvancedSearch);
            } else {
              // Si no hay término de búsqueda, recargar libros normalmente
              fetchBooks();
            }
          }}
          onClear={() => {
            clearSearch();
            // Recargar libros cuando se limpia la búsqueda
            fetchBooks();
          }}
          onToggleAdvanced={toggleAdvancedMode}
          isAdvancedMode={isAdvancedMode}
          suggestions={suggestions}
          searchHistory={searchHistory}
          isLoading={isLoading.search || searchLoading}
        />
        
        {isAdvancedMode && (
          <SearchFilters
            filters={filters}
            onFiltersChange={(filterName, value) => {
              updateFilters(filterName, value);
              // Ejecutar búsqueda inmediata cuando se cambian filtros
              const updatedFilters = { ...filters, [filterName]: value };
              if (searchTerm.trim() || Object.values(updatedFilters).some(v => v && v !== '')) {
                searchImmediately({ term: searchTerm, filters: updatedFilters }, handleAdvancedSearch);
              }
            }}
            onClearFilters={() => {
              clearAllFilters();
              // Recargar libros cuando se limpian todos los filtros
              if (searchTerm.trim()) {
                searchImmediately({ term: searchTerm, filters: {} }, handleAdvancedSearch);
              } else {
                fetchBooks();
              }
            }}
          />
        )}
        
        <FilterChips
          activeFilters={getActiveFilters()}
          onRemoveFilter={(filterName) => {
            removeFilter(filterName);
            // Ejecutar búsqueda después de remover filtro
            const updatedFilters = { ...filters, [filterName]: '' };
            if (searchTerm.trim() || Object.values(updatedFilters).some(v => v && v !== '')) {
              searchImmediately({ term: searchTerm, filters: updatedFilters }, handleAdvancedSearch);
            } else {
              fetchBooks();
            }
          }}
          onClearAll={() => {
            clearAllFilters();
            // Recargar libros cuando se limpian todos los filtros
            if (searchTerm.trim()) {
              searchImmediately({ term: searchTerm, filters: {} }, handleAdvancedSearch);
            } else {
              fetchBooks();
            }
          }}
        />
      </div>

      {error && <p className="error-message">{error}</p>}
      
      {/* Grid de libros - siempre visible si hay libros */}
      {safeBooks.length > 0 && (
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
                onClick={() => {
                        // Botón eliminar clickeado
                  handleDeleteClick(book.id, book.title);
                }} 
                className="delete-book-btn" 
                title="Eliminar libro"
                disabled={deletingBookId === book.id || selectionMode}
              >
                {deletingBookId === book.id ? '⋯' : '×'}
              </button>
              <button 
                onClick={() => handleEditBook(book)} 
                className="edit-book-btn" 
                title="Editar libro"
                disabled={selectionMode}
              >
                ✏️
              </button>
              <button 
                onClick={() => handleSearchCoverOnline(book)} 
                className="search-cover-btn" 
                title="Buscar portada online"
                disabled={selectionMode}
              >
                🔍
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
                
                {/* Botón RAG */}
                <RagButton 
                  book={book} 
                  onRagProcessed={(bookId, result) => {
                    console.log(`Libro ${bookId} procesado para RAG:`, result);
                    // Aquí podrías actualizar el estado local si es necesario
                  }}
                />
              </div>
            </div>
          );
        })}
        </div>
      )}

      {/* Mensaje si no hay libros */}
      {safeBooks.length === 0 && isInitialized && !error && (
        <div className="empty-state">
          <p>No se encontraron libros.</p>
        </div>
      )}

      {/* Controles de paginación */}
      {totalPages > 1 && (
        <PaginationControls
          currentPage={currentPage}
          totalPages={totalPages}
          totalItems={totalItems}
          perPage={perPage}
          onPageChange={goToPage}
          onPerPageChange={changePerPage}
          hasNext={paginationInfo.hasNext}
          hasPrev={paginationInfo.hasPrev}
          startItem={paginationInfo.startItem}
          endItem={paginationInfo.endItem}
          pageNumbers={paginationInfo.pageNumbers}
          showPerPageSelector={true}
          showInfo={true}
          className="library-pagination"
        />
      )}

      <DeleteConfirmationModal
        isOpen={deleteModal.isOpen}
        onClose={handleDeleteCancel}
        onConfirm={handleDeleteConfirm}
        bookTitle={deleteModal.bookTitle}
        isDeleting={deletingBookId !== null}
        isMultiple={deleteModal.isMultiple}
        selectedCount={deleteModal.selectedIds.length}
      />

      <BookEditModal
        isOpen={editModal.isOpen}
        onClose={handleCloseEditModal}
        book={editModal.book}
        onUpdate={handleBookUpdate}
        categories={categories}
        onCategoryCreate={handleCategoryCreate}
      />
    </div>
  );
}

export default LibraryView;
