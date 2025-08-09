import { useState, useEffect, useCallback } from 'react';
import { getBackendUrl } from '../config/api';

export const useBooks = (searchParams, debouncedSearchTerm) => {
  const [books, setBooks] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchBooks = useCallback(async () => {
    setLoading(true);
    setError('');
    
    const params = new URLSearchParams();
    const category = searchParams.get('category');

    if (category) {
      params.append('category', category);
    }
    if (debouncedSearchTerm) {
      params.append('search', debouncedSearchTerm);
    }

    const url = `${getBackendUrl()}/books/?${params.toString()}`;
    
    try {
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        // Validar que data sea un array antes de establecerlo
        if (Array.isArray(data)) {
          setBooks(data);
        } else {
          console.error('Respuesta del servidor no es un array:', data);
          setBooks([]);
          setError('Formato de respuesta inválido del servidor.');
        }
      } else {
        setError('No se pudieron cargar los libros.');
        setBooks([]);
      }
    } catch (err) {
      console.error('Error al cargar libros:', err);
      setError('Error de conexión al cargar la biblioteca.');
      setBooks([]);
    } finally {
      setLoading(false);
    }
  }, [debouncedSearchTerm, searchParams]);

  // Función para actualizar libros manualmente
  const refreshBooks = useCallback(() => {
    fetchBooks();
  }, [fetchBooks]);

  // Función para agregar un libro al estado local
  const addBook = useCallback((newBook) => {
    setBooks(prevBooks => {
      if (!Array.isArray(prevBooks)) return [newBook];
      return [newBook, ...prevBooks];
    });
  }, []);

  // Función para eliminar un libro del estado local
  const removeBook = useCallback((bookId) => {
    setBooks(prevBooks => {
      if (!Array.isArray(prevBooks)) return [];
      return prevBooks.filter(book => book.id !== bookId);
    });
  }, []);

  // Función para actualizar un libro en el estado local
  const updateBook = useCallback((bookId, updates) => {
    setBooks(prevBooks => {
      if (!Array.isArray(prevBooks)) return [];
      return prevBooks.map(book => 
        book.id === bookId ? { ...book, ...updates } : book
      );
    });
  }, []);

  return {
    books,
    error,
    loading,
    fetchBooks,
    refreshBooks,
    addBook,
    removeBook,
    updateBook
  };
}; 