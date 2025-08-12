import { useCallback } from 'react';
import { useAppMode } from '../contexts/AppModeContext';
import { getBackendUrl, checkBackendHealth } from '../config/api';

export const useBookService = () => {
  const { appMode, isLocalMode, isDriveMode } = useAppMode();

  const getBooks = useCallback(async (category = null, search = null, page = 1, perPage = 20) => {
    try {
      console.log('🔍 useBookService.getBooks llamado:', {
        category,
        search,
        page,
        perPage,
        isLocalMode,
        isDriveMode,
        appMode
      });
      
      // Verificar primero si el backend está disponible
      const backendAvailable = await checkBackendHealth();
      if (!backendAvailable) {
        throw new Error('Backend no disponible');
      }

      // Obtener la URL del backend dinámicamente
      const backendUrl = getBackendUrl();
      console.log('🌐 Backend URL:', backendUrl);

      if (isLocalMode) {
        let url = backendUrl ? `${backendUrl}/api/books/` : '/api/books/';
        const params = new URLSearchParams();
        if (category) params.append('category', category);
        if (search) params.append('search', search);
        params.append('page', page.toString());
        params.append('per_page', perPage.toString());
        
        console.log('📚 Llamando endpoint local:', `${url}?${params.toString()}`);
        
        const response = await fetch(`${url}?${params.toString()}`);
        
        if (!response.ok) {
          throw new Error('Error al obtener libros del servidor local');
        }
        const data = await response.json();
        console.log('✅ Respuesta del endpoint local:', data);
        return data;
      } else if (isDriveMode) {
        let url = backendUrl ? `${backendUrl}/api/drive/books/` : '/api/drive/books/';
        const params = new URLSearchParams();
        if (category) params.append('category', category);
        if (search) params.append('search', search);
        params.append('page', page.toString());
        params.append('per_page', perPage.toString());
        
        console.log('☁️ Llamando endpoint drive:', `${url}?${params.toString()}`);
        
        const response = await fetch(`${url}?${params.toString()}`);
        
        if (!response.ok) {
          throw new Error('Error al obtener libros de Google Drive');
        }
        const data = await response.json();
        console.log('✅ Respuesta del endpoint drive:', data);
        return data;
      }
    } catch (error) {
      // Solo mostrar error en consola si no es un error de conexión
      if (!error.message.includes('Backend no disponible') && !error.message.includes('Failed to fetch')) {
        console.error('Error en getBooks:', error);
      }
      throw error;
    }
  }, [isLocalMode, isDriveMode]);

  const uploadBook = useCallback(async (file) => {
    try {
      const formData = new FormData();
      formData.append('book_file', file);

      // Obtener la URL del backend dinámicamente
      const backendUrl = getBackendUrl();

      if (isLocalMode) {
        const url = backendUrl ? `${backendUrl}/api/upload-book-local/` : '/api/upload-book-local/';
        const response = await fetch(url, {
          method: 'POST',
          body: formData,
        });
        
        if (response.status === 409) {
          // Libro duplicado
          const errorData = await response.json();
          return {
            success: false,
            isDuplicate: true,
            detail: errorData.detail || 'Libro duplicado',
            title: errorData.title,
            author: errorData.author
          };
        }
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
      } else if (isDriveMode) {
        const url = backendUrl ? `${backendUrl}/api/drive/books/upload` : '/api/drive/books/upload';
        const response = await fetch(url, {
          method: 'POST',
          body: formData,
        });
        
        if (response.status === 409) {
          // Libro duplicado
          const errorData = await response.json();
          return {
            success: false,
            isDuplicate: true,
            detail: errorData.detail || 'Libro duplicado',
            title: errorData.title,
            author: errorData.author
          };
        }
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
      }
    } catch (error) {
      console.error('Error en uploadBook:', error);
      throw error;
    }
  }, [isLocalMode, isDriveMode]);

  const deleteBook = useCallback(async (bookId) => {
    try {
      // Obtener la URL del backend dinámicamente
      const backendUrl = getBackendUrl();

      if (isLocalMode) {
        const response = await fetch(`${backendUrl}/api/books/${bookId}`, {
          method: 'DELETE',
        });
        if (!response.ok) {
          throw new Error('Error al eliminar libro del servidor local');
        }
        return response;
      } else if (isDriveMode) {
        const response = await fetch(`${backendUrl}/api/drive/books/${bookId}`, {
          method: 'DELETE',
        });
        if (!response.ok) {
          throw new Error('Error al eliminar libro de Google Drive');
        }
        return response;
      }
    } catch (error) {
      console.error('Error en deleteBook:', error);
      throw error;
    }
  }, [isLocalMode, isDriveMode]);

  const getBookContent = useCallback(async (bookId) => {
    try {
      // Obtener la URL del backend dinámicamente
      const backendUrl = getBackendUrl();

      if (isLocalMode) {
        const response = await fetch(`${backendUrl}/api/books/download/${bookId}`);
        if (!response.ok) {
          throw new Error('Error al obtener contenido del libro local');
        }
        return await response.blob(); // Cambiar de text() a blob() para archivos binarios
      } else if (isDriveMode) {
        const response = await fetch(`${backendUrl}/api/drive/books/${bookId}/content`);
        if (!response.ok) {
          throw new Error('Error al obtener contenido del libro de Drive');
        }
        return await response.blob(); // Cambiar de json() a blob() para archivos binarios
      }
    } catch (error) {
      console.error('Error en getBookContent:', error);
      throw error;
    }
  }, [isLocalMode, isDriveMode]);

  const getCategories = useCallback(async () => {
    try {
      // Verificar primero si el backend está disponible
      const backendAvailable = await checkBackendHealth();
      if (!backendAvailable) {
        throw new Error('Backend no disponible');
      }

      // Obtener la URL del backend dinámicamente
      const backendUrl = getBackendUrl();

      if (isLocalMode) {
        const response = await fetch(`${backendUrl}/api/categories/`);
        if (!response.ok) {
          throw new Error('Error al obtener categorías del servidor local');
        }
        return await response.json();
      } else if (isDriveMode) {
        const response = await fetch(`${backendUrl}/api/drive/categories/`);
        if (!response.ok) {
          throw new Error('Error al obtener categorías de Google Drive');
        }
        return await response.json();
      }
    } catch (error) {
      // Solo mostrar error en consola si no es un error de conexión
      if (!error.message.includes('Backend no disponible') && !error.message.includes('Failed to fetch')) {
        console.error('Error en getCategories:', error);
      }
      throw error;
    }
  }, [isLocalMode, isDriveMode]);

  const updateBook = useCallback(async (bookId, bookData) => {
    try {
      // Obtener la URL del backend dinámicamente
      const backendUrl = getBackendUrl();

      const response = await fetch(`${backendUrl}/api/books/${bookId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(bookData)
      });

      if (!response.ok) {
        throw new Error('Error al actualizar el libro');
      }

      return await response.json();
    } catch (error) {
      console.error('Error en updateBook:', error);
      throw error;
    }
  }, []);

  const updateBookCover = useCallback(async (bookId, coverFile) => {
    try {
      const formData = new FormData();
      formData.append('cover_file', coverFile);

      // Obtener la URL del backend dinámicamente
      const backendUrl = getBackendUrl();

      const response = await fetch(`${backendUrl}/api/books/${bookId}/update-cover`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Error al actualizar la portada');
      }

      return await response.json();
    } catch (error) {
      console.error('Error en updateBookCover:', error);
      throw error;
    }
  }, []);

  const createCategory = useCallback(async (categoryName) => {
    try {
      // Obtener la URL del backend dinámicamente
      const backendUrl = getBackendUrl();

      const response = await fetch(`${backendUrl}/api/categories/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: categoryName })
      });

      if (!response.ok) {
        throw new Error('Error al crear la categoría');
      }

      return await response.json();
    } catch (error) {
      console.error('Error en createCategory:', error);
      throw error;
    }
  }, []);

  const openLocalBook = useCallback(async (bookId) => {
    try {
      // Obtener la URL del backend dinámicamente
      const backendUrl = getBackendUrl();

      const response = await fetch(`${backendUrl}/api/books/${bookId}/open`);
      
      if (!response.ok) {
        throw new Error('Error al abrir el libro');
      }

      return await response.blob();
    } catch (error) {
      console.error('Error en openLocalBook:', error);
      throw error;
    }
  }, []);

  const cleanupTempFiles = useCallback(async () => {
    try {
      // Obtener la URL del backend dinámicamente
      const backendUrl = getBackendUrl();

      const response = await fetch(`${backendUrl}/api/cleanup-temp-files`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Error al limpiar archivos temporales');
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Error limpiando archivos temporales:', error);
      throw error;
    }
  }, []);

  return {
    appMode,
    isLocalMode,
    isDriveMode,
    getBooks,
    uploadBook,
    deleteBook,
    getBookContent,
    getCategories,
    updateBook,
    updateBookCover,
    createCategory,
    openLocalBook,
    cleanupTempFiles,
  };
}; 