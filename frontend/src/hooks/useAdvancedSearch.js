import { useState, useCallback, useRef, useEffect } from 'react';
import { useAppMode } from '../contexts/AppModeContext';

const useAdvancedSearch = () => {
  const { isLocalMode, isDriveMode } = useAppMode();
  
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
  const [searchHistory, setSearchHistory] = useState([]);
  const [activeFilters, setActiveFilters] = useState([]);
  
  // Estados de carga
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState(null);
  
  // Cache y optimización
  const searchCache = useRef(new Map());
  const debounceTimeout = useRef(null);

  // Constantes
  const DEBOUNCE_DELAY = 300;
  const MAX_HISTORY_ITEMS = 10;
  const CACHE_EXPIRY = 5 * 60 * 1000; // 5 minutos

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

  // Función para realizar búsqueda avanzada (simplificada)
  const performAdvancedSearch = useCallback(async (searchParams) => {
    setIsSearching(true);
    setSearchError(null);

    try {
      const params = new URLSearchParams();
      
      // Parámetros de búsqueda básica
      if (searchParams.term) {
        params.append('search', searchParams.term);
      }
      
      // Parámetros de paginación
      if (searchParams.page) {
        params.append('page', searchParams.page);
      }
      if (searchParams.perPage) {
        params.append('per_page', searchParams.perPage);
      }

      // Usar el endpoint de búsqueda simple existente
      const endpoint = isLocalMode 
        ? `http://localhost:8001/api/books/?${params.toString()}`
        : `http://localhost:8001/api/drive/books/?${params.toString()}`;

      const response = await fetch(endpoint);
      
      if (!response.ok) {
        throw new Error(`Error en búsqueda: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      setSearchError(error.message);
      throw error;
    } finally {
      setIsSearching(false);
    }
  }, [isLocalMode, isDriveMode]);

  // Función para búsqueda con debounce
  const debouncedSearch = useCallback((searchParams) => {
    if (debounceTimeout.current) {
      clearTimeout(debounceTimeout.current);
    }

    return new Promise((resolve, reject) => {
      debounceTimeout.current = setTimeout(async () => {
        try {
          const result = await performAdvancedSearch(searchParams);
          resolve(result);
        } catch (error) {
          reject(error);
        }
      }, DEBOUNCE_DELAY);
    });
  }, [performAdvancedSearch]);

  // Función para búsqueda inmediata
  const searchImmediately = useCallback(async (searchParams) => {
    if (debounceTimeout.current) {
      clearTimeout(debounceTimeout.current);
    }
    return await performAdvancedSearch(searchParams);
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
    updateSearchTerm: setSearchTerm,
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