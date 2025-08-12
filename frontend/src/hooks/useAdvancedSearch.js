import { useState, useCallback, useRef, useEffect } from 'react';

const useAdvancedSearch = () => {
  // Estados principales
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    category: '',
    author: '',
    dateFrom: '',
    dateTo: '',
    fileType: '',
    source: '',
    hasCover: false,
    hasFile: false
  });
  
  // Estados de UI
  const [isAdvancedMode, setIsAdvancedMode] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [searchHistory] = useState([]);
  const [activeFilters, setActiveFilters] = useState([]);
  
  // Estados de carga
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState(null);
  
  // Cache y optimización
  const debounceTimeout = useRef(null);
  const searchInProgress = useRef(false);
  const lastSearchRef = useRef({ term: '', filters: {}, timestamp: 0 });
  const searchCacheRef = useRef(new Map());

  // Constantes
  const DEBOUNCE_DELAY = 500; // Aumentado para evitar búsquedas muy frecuentes
  const CACHE_EXPIRY_TIME = 5 * 60 * 1000; // 5 minutos en milisegundos

  // Función para obtener etiqueta de filtro
  const getFilterLabel = useCallback((filterName, value) => {
    const labels = {
      category: `Categoría: ${value}`,
      author: `Autor: ${value}`,
      dateFrom: `Desde: ${value}`,
      dateTo: `Hasta: ${value}`,
      fileType: `Tipo: ${value}`,
      source: `Fuente: ${value}`,
      hasCover: 'Con portada',
      hasFile: 'Con archivo'
    };
    return labels[filterName] || `${filterName}: ${value}`;
  }, []);

  // Función para actualizar filtros
  const updateFilter = useCallback((filterName, value) => {
    setFilters(prev => {
      const newFilters = { ...prev, [filterName]: value };
      
      // Actualizar filtros activos
      const newActiveFilters = Object.entries(newFilters)
        .filter(([key, val]) => val && val !== '')
        .map(([key, val]) => ({ name: key, value: val, label: getFilterLabel(key, val) }));
      
      setActiveFilters(newActiveFilters);
      return newFilters;
    });
  }, [getFilterLabel]);

  // Función para limpiar filtros
  const clearFilters = useCallback(() => {
    setFilters({
      category: '',
      author: '',
      dateFrom: '',
      dateTo: '',
      fileType: '',
      source: '',
      hasCover: false,
      hasFile: false
    });
    setActiveFilters([]);
  }, []);

  // Función para remover filtro específico
  const removeFilter = useCallback((filterName) => {
    setFilters(prev => {
      const newFilters = { ...prev, [filterName]: '' };
      const newActiveFilters = activeFilters.filter(f => f.name !== filterName);
      setActiveFilters(newActiveFilters);
      return newFilters;
    });
  }, [activeFilters]);

  // Función para obtener sugerencias (simplificada)
  const fetchSuggestions = useCallback(async (term) => {
    if (!term || term.length < 2) {
      setSuggestions([]);
      return;
    }

    // Por ahora, generar sugerencias básicas basadas en el término
    const basicSuggestions = [
      term,
      `${term} libro`,
      `${term} pdf`,
      `${term} autor`
    ];
    
    setSuggestions(basicSuggestions);
  }, []);

  // Función para generar clave de cache
  const generateCacheKey = useCallback((term, searchFilters) => {
    return JSON.stringify({ term: term.trim().toLowerCase(), filters: searchFilters });
  }, []);

  // Función para verificar si es la misma búsqueda
  const isSameSearch = useCallback((term, searchFilters) => {
    const currentSearch = { term: term.trim(), filters: searchFilters };
    const lastSearch = lastSearchRef.current;
    
    return (
      currentSearch.term === lastSearch.term &&
      JSON.stringify(currentSearch.filters) === JSON.stringify(lastSearch.filters) &&
      Date.now() - lastSearch.timestamp < 1000 // Evitar búsquedas duplicadas en menos de 1 segundo
    );
  }, []);

  // Función para obtener resultado desde cache
  const getCachedResult = useCallback((cacheKey) => {
    const cached = searchCacheRef.current.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < CACHE_EXPIRY_TIME) {
      return cached.result;
    }
    return null;
  }, [CACHE_EXPIRY_TIME]);

  // Función para guardar en cache
  const setCachedResult = useCallback((cacheKey, result) => {
    searchCacheRef.current.set(cacheKey, {
      result,
      timestamp: Date.now()
    });
    
    // Limpiar cache antiguo (mantener solo los últimos 20 resultados)
    if (searchCacheRef.current.size > 20) {
      const entries = Array.from(searchCacheRef.current.entries());
      entries.sort((a, b) => b[1].timestamp - a[1].timestamp);
      
      const newCache = new Map();
      entries.slice(0, 20).forEach(([key, value]) => {
        newCache.set(key, value);
      });
      searchCacheRef.current = newCache;
    }
  }, []);

  // Función para búsqueda avanzada
  const performAdvancedSearch = useCallback(async (searchParams, onSearchCallback) => {
    const { term = searchTerm, filters: searchFilters = filters } = searchParams || {};
    
    // Verificar si es la misma búsqueda que la anterior
    if (isSameSearch(term, searchFilters)) {
      return;
    }

    // Verificar si hay una búsqueda en progreso
    if (searchInProgress.current) {
      return;
    }

    // Verificar cache
    const cacheKey = generateCacheKey(term, searchFilters);
    const cachedResult = getCachedResult(cacheKey);
    
    if (cachedResult) {
      // Actualizar referencia de última búsqueda
      lastSearchRef.current = { term, filters: searchFilters, timestamp: Date.now() };
      return cachedResult;
    }

    setIsSearching(true);
    setSearchError(null);
    searchInProgress.current = true;
    
    try {
      let results;
      
      // Llamar al callback de búsqueda proporcionado por el componente padre
      if (onSearchCallback && typeof onSearchCallback === 'function') {
        results = await onSearchCallback({ term, filters: searchFilters });
      } else {
        // Implementación por defecto si no se proporciona callback
        results = [];
      }
      
      // Guardar en cache
      setCachedResult(cacheKey, results);
      
      // Actualizar referencia de última búsqueda
      lastSearchRef.current = { term, filters: searchFilters, timestamp: Date.now() };
      
      return results;
    } catch (error) {
      setSearchError(error.message);
      throw error;
    } finally {
      setIsSearching(false);
      searchInProgress.current = false;
    }
  }, [searchTerm, filters, isSameSearch, generateCacheKey, getCachedResult, setCachedResult]);

  // Función para búsqueda con debounce mejorado
  const debouncedSearch = useCallback((searchParams, onSearchCallback) => {
    if (debounceTimeout.current) {
      clearTimeout(debounceTimeout.current);
    }

    return new Promise((resolve, reject) => {
      debounceTimeout.current = setTimeout(async () => {
        try {
          const result = await performAdvancedSearch(searchParams, onSearchCallback);
          resolve(result);
        } catch (error) {
          reject(error);
        }
      }, DEBOUNCE_DELAY);
    });
  }, [performAdvancedSearch]);

  // Función para búsqueda inmediata
  const searchImmediately = useCallback(async (searchParams, onSearchCallback) => {
    if (debounceTimeout.current) {
      clearTimeout(debounceTimeout.current);
    }
    return await performAdvancedSearch(searchParams, onSearchCallback);
  }, [performAdvancedSearch]);

  // Función para obtener metadatos de filtros (simplificada)
  const getFilterMetadata = useCallback(async () => {
    // Por ahora, devolver metadatos básicos
    return {
      categories: ['Ficción', 'No Ficción', 'Ciencia', 'Historia', 'Tecnología'],
      authors: [],
      fileTypes: ['pdf', 'epub', 'txt'],
      sources: ['local', 'drive']
    };
  }, []);

  // Función para actualizar término de búsqueda con debounce
  const updateSearchTerm = useCallback((newTerm) => {
    setSearchTerm(newTerm);
    
    // Limpiar timeout anterior
    if (debounceTimeout.current) {
      clearTimeout(debounceTimeout.current);
    }
    
    // Solo mostrar sugerencias si hay texto
    if (newTerm.trim().length >= 2) {
      setShowSuggestions(true);
      // setShowHistory(false); // This state doesn't exist in the original file
    } else {
      setShowSuggestions(false);
      // setShowHistory(false); // This state doesn't exist in the original file
    }
  }, []);

  // Efecto para limpiar timeout al desmontar
  useEffect(() => {
    return () => {
      if (debounceTimeout.current) {
        clearTimeout(debounceTimeout.current);
      }
    };
  }, []);

  return {
    // Estados
    searchTerm,
    filters,
    suggestions,
    searchHistory,
    isAdvancedMode,
    showSuggestions,
    isLoading: isSearching,
    searchError,
    
    // Acciones de búsqueda
    setSearchTerm,
    updateSearchTerm, // Usar la nueva función con debounce
    updateFilters: updateFilter,
    setShowSuggestions,
    setIsAdvancedMode,
    clearSearch: () => {
      setSearchTerm('');
      setFilters({
        category: '',
        author: '',
        dateFrom: '',
        dateTo: '',
        fileType: '',
        source: '',
        hasCover: false,
        hasFile: false
      });
      setActiveFilters([]);
      // Limpiar timeout al limpiar búsqueda
      if (debounceTimeout.current) {
        clearTimeout(debounceTimeout.current);
      }
      // Limpiar cache
      searchCacheRef.current.clear();
      lastSearchRef.current = { term: '', filters: {}, timestamp: 0 };
    },
    clearAllFilters: clearFilters,
    removeFilter,
    toggleAdvancedMode: () => setIsAdvancedMode(!isAdvancedMode),
    getActiveFilters: () => activeFilters,
    
    // Funciones de búsqueda
    performSearch: debouncedSearch,
    searchImmediately,
    fetchSuggestions,
    getFilterMetadata,
    
    // Utilidades
    hasActiveFilters: activeFilters.length > 0,
    hasSearchTerm: searchTerm.trim().length > 0,
    isSearchingOrHasResults: isSearching || searchHistory.length > 0
  };
};

export default useAdvancedSearch; 