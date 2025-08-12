import { useState, useCallback, useRef, useEffect } from 'react';

const useBookSearch = (fetchBooks, withLoading) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({});
  const [isSearching, setIsSearching] = useState(false);
  
  // Refs para controlar el estado de búsqueda
  const searchTimeoutRef = useRef(null);
  const searchInProgressRef = useRef(false);
  const lastSearchRef = useRef({ term: '', filters: {} });

  // Constantes
  const SEARCH_DELAY = 600; // Delay para evitar búsquedas muy frecuentes

  // Función para actualizar término de búsqueda
  const updateSearchTerm = useCallback((newTerm) => {
    setSearchTerm(newTerm);
  }, []);

  // Función para actualizar filtros
  const updateFilters = useCallback((newFilters) => {
    setFilters(newFilters);
  }, []);

  // Función para limpiar búsqueda
  const clearSearch = useCallback(() => {
    setSearchTerm('');
    setFilters({});
    
    // Limpiar timeout si existe
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
      searchTimeoutRef.current = null;
    }
  }, []);

  // Función para ejecutar búsqueda
  const executeSearch = useCallback(async (term, searchFilters) => {
    // Evitar búsquedas duplicadas
    if (searchInProgressRef.current) {
      return;
    }

    // Verificar si la búsqueda es diferente a la última
    const currentSearch = { term, filters: searchFilters };
    const lastSearch = lastSearchRef.current;
    
    if (JSON.stringify(currentSearch) === JSON.stringify(lastSearch)) {
      return; // Misma búsqueda, no hacer nada
    }

    searchInProgressRef.current = true;
    setIsSearching(true);

    try {
      await withLoading('search', () => fetchBooks());
      lastSearchRef.current = currentSearch;
    } catch (error) {
      console.error('Error en búsqueda:', error);
    } finally {
      setIsSearching(false);
      searchInProgressRef.current = false;
    }
  }, [fetchBooks, withLoading]);

  // Efecto para manejar búsqueda con debounce
  useEffect(() => {
    // Limpiar timeout anterior
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    // Solo hacer búsqueda si hay término o filtros
    if (searchTerm || Object.keys(filters).length > 0) {
      searchTimeoutRef.current = setTimeout(() => {
        executeSearch(searchTerm, filters);
      }, SEARCH_DELAY);
    }

    // Cleanup
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchTerm, filters, executeSearch]);

  // Función para búsqueda inmediata (sin debounce)
  const searchImmediately = useCallback(async (term, searchFilters) => {
    // Limpiar timeout si existe
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
      searchTimeoutRef.current = null;
    }

    await executeSearch(term, searchFilters);
  }, [executeSearch]);

  return {
    // Estados
    searchTerm,
    filters,
    isSearching,
    
    // Acciones
    updateSearchTerm,
    updateFilters,
    clearSearch,
    searchImmediately,
    
    // Utilidades
    hasSearchCriteria: searchTerm || Object.keys(filters).length > 0
  };
};

export default useBookSearch;
