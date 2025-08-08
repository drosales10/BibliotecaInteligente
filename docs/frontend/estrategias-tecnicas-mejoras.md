# Estrategias Técnicas - Mejoras de Interfaz

## 📋 Resumen

Este documento detalla las estrategias técnicas específicas para implementar cada mejora de la interfaz de la Biblioteca Inteligente, incluyendo patrones de diseño, algoritmos y mejores prácticas.

## 🚀 Fase 1: Optimización de Rendimiento

### 1.1 Estrategia de Paginación Backend

#### Patrón de Implementación
```python
# Patrón Repository con Paginación
class BookRepository:
    def get_books_paginated(self, offset: int, limit: int, filters: dict):
        query = self._build_query(filters)
        total = query.count()
        books = query.offset(offset).limit(limit).all()
        return books, total
    
    def _build_query(self, filters: dict):
        query = self.db.query(Book)
        if filters.get('category'):
            query = query.filter(Book.category == filters['category'])
        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Book.title.ilike(search_term),
                    Book.author.ilike(search_term)
                )
            )
        return query.order_by(Book.id.desc())
```

#### Optimizaciones de Base de Datos
- **Índices compuestos**: `(category, title, author)`
- **Índices de búsqueda**: `(title, author)` para búsquedas
- **Índices de fecha**: `(upload_date)` para ordenamiento
- **Query optimization**: Usar `EXPLAIN` para analizar consultas

#### Estrategia de Caché
```python
# Caché de consultas frecuentes
from functools import lru_cache
import redis

class CachedBookRepository:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.cache_ttl = 300  # 5 minutos
    
    def get_books_paginated(self, offset: int, limit: int, filters: dict):
        cache_key = self._generate_cache_key(offset, limit, filters)
        
        # Intentar obtener del caché
        cached_result = self.redis.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
        
        # Obtener de base de datos
        result = self._fetch_from_db(offset, limit, filters)
        
        # Guardar en caché
        self.redis.setex(cache_key, self.cache_ttl, json.dumps(result))
        return result
```

### 1.2 Estrategia de Paginación Frontend

#### Hook de Paginación Inteligente
```javascript
// usePagination.js - Hook personalizado
export const usePagination = (initialConfig = {}) => {
  const {
    initialPage = 1,
    initialLimit = 20,
    maxLimit = 100,
    debounceMs = 300
  } = initialConfig;

  const [state, setState] = useState({
    page: initialPage,
    limit: initialLimit,
    total: 0,
    loading: false,
    error: null
  });

  const [debouncedPage, setDebouncedPage] = useState(initialPage);

  // Debounce para evitar múltiples requests
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedPage(state.page);
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [state.page, debounceMs]);

  const pagination = useMemo(() => ({
    page: state.page,
    limit: state.limit,
    total: state.total,
    pages: Math.ceil(state.total / state.limit),
    hasNext: state.page * state.limit < state.total,
    hasPrev: state.page > 1,
    startIndex: (state.page - 1) * state.limit + 1,
    endIndex: Math.min(state.page * state.limit, state.total)
  }), [state.page, state.limit, state.total]);

  const setPage = useCallback((newPage) => {
    setState(prev => ({ ...prev, page: Math.max(1, newPage) }));
  }, []);

  const setLimit = useCallback((newLimit) => {
    const validLimit = Math.min(Math.max(1, newLimit), maxLimit);
    setState(prev => ({ 
      ...prev, 
      limit: validLimit,
      page: 1 // Reset a primera página
    }));
  }, [maxLimit]);

  return {
    ...state,
    pagination,
    setPage,
    setLimit,
    setTotal: (total) => setState(prev => ({ ...prev, total })),
    setLoading: (loading) => setState(prev => ({ ...prev, loading })),
    setError: (error) => setState(prev => ({ ...prev, error }))
  };
};
```

#### Componente de Controles de Paginación
```javascript
// PaginationControls.js
const PaginationControls = ({ pagination, onPageChange, onLimitChange }) => {
  const { page, pages, hasNext, hasPrev, total, limit } = pagination;
  
  // Generar rango de páginas visibles
  const getVisiblePages = () => {
    const delta = 2; // Páginas a mostrar a cada lado
    const range = [];
    const rangeWithDots = [];

    for (let i = Math.max(2, page - delta); 
         i <= Math.min(pages - 1, page + delta); 
         i++) {
      range.push(i);
    }

    if (page - delta > 2) {
      rangeWithDots.push(1, '...');
    } else {
      rangeWithDots.push(1);
    }

    rangeWithDots.push(...range);

    if (page + delta < pages - 1) {
      rangeWithDots.push('...', pages);
    } else if (pages > 1) {
      rangeWithDots.push(pages);
    }

    return rangeWithDots;
  };

  return (
    <div className="pagination-controls">
      <div className="pagination-info">
        Mostrando {((page - 1) * limit) + 1} - {Math.min(page * limit, total)} de {total} libros
      </div>
      
      <div className="pagination-buttons">
        <button 
          onClick={() => onPageChange(1)}
          disabled={!hasPrev}
          className="pagination-btn"
        >
          ⏮️ Primera
        </button>
        
        <button 
          onClick={() => onPageChange(page - 1)}
          disabled={!hasPrev}
          className="pagination-btn"
        >
          ◀️ Anterior
        </button>

        {getVisiblePages().map((pageNum, index) => (
          <button
            key={index}
            onClick={() => typeof pageNum === 'number' && onPageChange(pageNum)}
            disabled={pageNum === '...'}
            className={`pagination-btn ${pageNum === page ? 'active' : ''}`}
          >
            {pageNum}
          </button>
        ))}

        <button 
          onClick={() => onPageChange(page + 1)}
          disabled={!hasNext}
          className="pagination-btn"
        >
          Siguiente ▶️
        </button>
        
        <button 
          onClick={() => onPageChange(pages)}
          disabled={!hasNext}
          className="pagination-btn"
        >
          Última ⏭️
        </button>
      </div>

      <div className="pagination-limit">
        <label>Libros por página:</label>
        <select 
          value={limit} 
          onChange={(e) => onLimitChange(parseInt(e.target.value))}
        >
          <option value={10}>10</option>
          <option value={20}>20</option>
          <option value={50}>50</option>
          <option value={100}>100</option>
        </select>
      </div>
    </div>
  );
};
```

### 1.3 Estrategia de Lazy Loading de Imágenes

#### Hook de Intersection Observer
```javascript
// useIntersectionObserver.js
export const useIntersectionObserver = (options = {}) => {
  const [isIntersecting, setIsIntersecting] = useState(false);
  const [hasIntersected, setHasIntersected] = useState(false);
  const elementRef = useRef(null);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasIntersected) {
          setIsIntersecting(true);
          setHasIntersected(true);
        }
      },
      {
        rootMargin: '50px', // Precargar 50px antes
        threshold: 0.1,
        ...options
      }
    );

    observer.observe(element);

    return () => {
      observer.unobserve(element);
    };
  }, [hasIntersected, options]);

  return [elementRef, isIntersecting];
};
```

#### Componente de Imagen Lazy
```javascript
// LazyImage.js
const LazyImage = ({ 
  src, 
  alt, 
  placeholder = null, 
  fallback = null,
  className = '',
  onLoad,
  onError 
}) => {
  const [imageRef, isIntersecting] = useIntersectionObserver();
  const [imageState, setImageState] = useState('loading'); // loading, loaded, error
  const [currentSrc, setCurrentSrc] = useState(null);

  useEffect(() => {
    if (isIntersecting && !currentSrc) {
      setCurrentSrc(src);
    }
  }, [isIntersecting, src, currentSrc]);

  const handleLoad = () => {
    setImageState('loaded');
    onLoad?.();
  };

  const handleError = () => {
    setImageState('error');
    onError?.();
  };

  if (!isIntersecting) {
    return (
      <div ref={imageRef} className={`lazy-image-placeholder ${className}`}>
        {placeholder || <ImageSkeleton />}
      </div>
    );
  }

  if (imageState === 'error' && fallback) {
    return (
      <img 
        src={fallback} 
        alt={alt} 
        className={`lazy-image fallback ${className}`}
      />
    );
  }

  return (
    <img
      ref={imageRef}
      src={currentSrc}
      alt={alt}
      className={`lazy-image ${imageState} ${className}`}
      onLoad={handleLoad}
      onError={handleError}
      style={{
        opacity: imageState === 'loaded' ? 1 : 0,
        transition: 'opacity 0.3s ease-in-out'
      }}
    />
  );
};
```

#### Componente Skeleton para Imágenes
```javascript
// ImageSkeleton.js
const ImageSkeleton = ({ width = 200, height = 300, className = '' }) => {
  return (
    <div 
      className={`image-skeleton ${className}`}
      style={{ 
        width, 
        height,
        background: 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
        backgroundSize: '200% 100%',
        animation: 'shimmer 1.5s infinite'
      }}
    />
  );
};

// CSS para la animación shimmer
const shimmerStyles = `
  @keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
  }
`;
```

## 🎨 Fase 2: Mejoras de UX/UI

### 2.1 Estrategia de Indicadores de Carga

#### Skeleton Loader para Tarjetas
```javascript
// BookCardSkeleton.js
const BookCardSkeleton = ({ count = 1 }) => {
  const skeletons = Array.from({ length: count }, (_, index) => (
    <div key={index} className="book-card-skeleton">
      <div className="skeleton-cover"></div>
      <div className="skeleton-content">
        <div className="skeleton-title"></div>
        <div className="skeleton-author"></div>
        <div className="skeleton-category"></div>
        <div className="skeleton-actions">
          <div className="skeleton-button"></div>
          <div className="skeleton-button"></div>
        </div>
      </div>
    </div>
  ));

  return <>{skeletons}</>;
};
```

#### Hook de Estado de Carga
```javascript
// useLoadingState.js
export const useLoadingState = (initialState = {}) => {
  const [loadingStates, setLoadingStates] = useState(initialState);

  const setLoading = useCallback((key, isLoading) => {
    setLoadingStates(prev => ({
      ...prev,
      [key]: isLoading
    }));
  }, []);

  const setMultipleLoading = useCallback((states) => {
    setLoadingStates(prev => ({
      ...prev,
      ...states
    }));
  }, []);

  const isLoading = useCallback((key) => {
    return loadingStates[key] || false;
  }, [loadingStates]);

  const isAnyLoading = useCallback(() => {
    return Object.values(loadingStates).some(Boolean);
  }, [loadingStates]);

  return {
    loadingStates,
    setLoading,
    setMultipleLoading,
    isLoading,
    isAnyLoading
  };
};
```

### 2.2 Estrategia de Búsqueda Avanzada

#### Hook de Búsqueda con Debounce
```javascript
// useAdvancedSearch.js
export const useAdvancedSearch = (options = {}) => {
  const {
    debounceMs = 300,
    minSearchLength = 2,
    maxResults = 50
  } = options;

  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    category: '',
    author: '',
    dateFrom: '',
    dateTo: '',
    source: 'all' // 'all', 'local', 'drive'
  });
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);

  const debouncedSearchTerm = useDebounce(searchTerm, debounceMs);

  // Búsqueda principal
  useEffect(() => {
    if (debouncedSearchTerm.length >= minSearchLength || 
        Object.values(filters).some(v => v !== '' && v !== 'all')) {
      performSearch();
    } else {
      setResults([]);
    }
  }, [debouncedSearchTerm, filters]);

  const performSearch = useCallback(async () => {
    setLoading(true);
    try {
      const searchParams = new URLSearchParams({
        search: debouncedSearchTerm,
        ...filters
      });

      const response = await fetch(`/api/books/search?${searchParams}`);
      const data = await response.json();
      
      setResults(data.books || []);
    } catch (error) {
      console.error('Error en búsqueda:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [debouncedSearchTerm, filters]);

  // Autocompletado
  const getSuggestions = useCallback(async (term) => {
    if (term.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      const response = await fetch(`/api/books/suggestions?q=${term}`);
      const data = await response.json();
      setSuggestions(data.suggestions || []);
    } catch (error) {
      console.error('Error obteniendo sugerencias:', error);
      setSuggestions([]);
    }
  }, []);

  return {
    searchTerm,
    setSearchTerm,
    filters,
    setFilters,
    results,
    loading,
    suggestions,
    getSuggestions,
    clearSearch: () => {
      setSearchTerm('');
      setFilters({
        category: '',
        author: '',
        dateFrom: '',
        dateTo: '',
        source: 'all'
      });
    }
  };
};
```

#### Componente de Filtros Avanzados
```javascript
// SearchFilters.js
const SearchFilters = ({ filters, onFiltersChange, categories }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleFilterChange = (key, value) => {
    onFiltersChange({
      ...filters,
      [key]: value
    });
  };

  return (
    <div className="search-filters">
      <button 
        className="filters-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {isExpanded ? 'Ocultar' : 'Mostrar'} Filtros Avanzados
        <span className={`toggle-icon ${isExpanded ? 'expanded' : ''}`}>
          ▼
        </span>
      </button>

      {isExpanded && (
        <div className="filters-panel">
          <div className="filter-group">
            <label>Categoría:</label>
            <select 
              value={filters.category} 
              onChange={(e) => handleFilterChange('category', e.target.value)}
            >
              <option value="">Todas las categorías</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Autor:</label>
            <input
              type="text"
              value={filters.author}
              onChange={(e) => handleFilterChange('author', e.target.value)}
              placeholder="Buscar por autor..."
            />
          </div>

          <div className="filter-group">
            <label>Fuente:</label>
            <select 
              value={filters.source} 
              onChange={(e) => handleFilterChange('source', e.target.value)}
            >
              <option value="all">Todas las fuentes</option>
              <option value="local">Solo locales</option>
              <option value="drive">Solo Drive</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Fecha desde:</label>
            <input
              type="date"
              value={filters.dateFrom}
              onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
            />
          </div>

          <div className="filter-group">
            <label>Fecha hasta:</label>
            <input
              type="date"
              value={filters.dateTo}
              onChange={(e) => handleFilterChange('dateTo', e.target.value)}
            />
          </div>

          <button 
            className="clear-filters"
            onClick={() => onFiltersChange({
              category: '',
              author: '',
              dateFrom: '',
              dateTo: '',
              source: 'all'
            })}
          >
            Limpiar Filtros
          </button>
        </div>
      )}
    </div>
  );
};
```

### 2.3 Estrategia de Diseño Responsive

#### Hook de Breakpoints
```javascript
// useBreakpoints.js
export const useBreakpoints = () => {
  const [breakpoint, setBreakpoint] = useState('desktop');

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      if (width < 768) {
        setBreakpoint('mobile');
      } else if (width < 1024) {
        setBreakpoint('tablet');
      } else {
        setBreakpoint('desktop');
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return {
    breakpoint,
    isMobile: breakpoint === 'mobile',
    isTablet: breakpoint === 'tablet',
    isDesktop: breakpoint === 'desktop'
  };
};
```

#### Grid Responsive Inteligente
```javascript
// ResponsiveGrid.js
const ResponsiveGrid = ({ children, className = '' }) => {
  const { isMobile, isTablet, isDesktop } = useBreakpoints();

  const gridConfig = {
    mobile: { columns: 1, gap: '1rem' },
    tablet: { columns: 2, gap: '1.5rem' },
    desktop: { columns: 4, gap: '2rem' }
  };

  const currentConfig = isMobile ? gridConfig.mobile : 
                       isTablet ? gridConfig.tablet : 
                       gridConfig.desktop;

  return (
    <div 
      className={`responsive-grid ${className}`}
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${currentConfig.columns}, 1fr)`,
        gap: currentConfig.gap,
        padding: isMobile ? '1rem' : '2rem'
      }}
    >
      {children}
    </div>
  );
};
```

## ⚡ Fase 3: Optimizaciones Avanzadas

### 3.1 Estrategia de Virtualización

#### Implementación con react-window
```javascript
// VirtualizedBookGrid.js
import { FixedSizeGrid as Grid } from 'react-window';

const VirtualizedBookGrid = ({ books, containerWidth, containerHeight }) => {
  const { isMobile, isTablet, isDesktop } = useBreakpoints();
  
  const columnCount = isMobile ? 1 : isTablet ? 2 : 4;
  const rowCount = Math.ceil(books.length / columnCount);
  
  const columnWidth = containerWidth / columnCount;
  const rowHeight = 400; // Altura fija de cada tarjeta

  const Cell = ({ columnIndex, rowIndex, style }) => {
    const bookIndex = rowIndex * columnCount + columnIndex;
    const book = books[bookIndex];

    if (!book) return null;

    return (
      <div style={style}>
        <BookCard book={book} />
      </div>
    );
  };

  return (
    <Grid
      columnCount={columnCount}
      columnWidth={columnWidth}
      height={containerHeight}
      rowCount={rowCount}
      rowHeight={rowHeight}
      width={containerWidth}
    >
      {Cell}
    </Grid>
  );
};
```

### 3.2 Estrategia de Caché Inteligente

#### Hook de Caché con Invalidación
```javascript
// useCache.js
export const useCache = (options = {}) => {
  const {
    ttl = 5 * 60 * 1000, // 5 minutos
    maxSize = 100,
    storage = 'sessionStorage'
  } = options;

  const [cache, setCache] = useState(new Map());
  const [timestamps, setTimestamps] = useState(new Map());

  const get = useCallback((key) => {
    const item = cache.get(key);
    const timestamp = timestamps.get(key);
    
    if (!item || !timestamp) return null;
    
    const isExpired = Date.now() - timestamp > ttl;
    if (isExpired) {
      remove(key);
      return null;
    }
    
    return item;
  }, [cache, timestamps, ttl]);

  const set = useCallback((key, value) => {
    // Limpiar caché si excede el tamaño máximo
    if (cache.size >= maxSize) {
      const oldestKey = timestamps.keys().next().value;
      remove(oldestKey);
    }
    
    setCache(prev => new Map(prev.set(key, value)));
    setTimestamps(prev => new Map(prev.set(key, Date.now())));
    
    // Persistir en storage
    if (storage === 'localStorage') {
      localStorage.setItem(`cache_${key}`, JSON.stringify({
        value,
        timestamp: Date.now()
      }));
    }
  }, [cache, timestamps, maxSize, storage]);

  const remove = useCallback((key) => {
    setCache(prev => {
      const newCache = new Map(prev);
      newCache.delete(key);
      return newCache;
    });
    
    setTimestamps(prev => {
      const newTimestamps = new Map(prev);
      newTimestamps.delete(key);
      return newTimestamps;
    });
    
    if (storage === 'localStorage') {
      localStorage.removeItem(`cache_${key}`);
    }
  }, [storage]);

  const clear = useCallback(() => {
    setCache(new Map());
    setTimestamps(new Map());
    
    if (storage === 'localStorage') {
      Object.keys(localStorage)
        .filter(key => key.startsWith('cache_'))
        .forEach(key => localStorage.removeItem(key));
    }
  }, [storage]);

  return { get, set, remove, clear, size: cache.size };
};
```

### 3.3 Estrategia de Actualización Automática

#### Hook de Polling Inteligente
```javascript
// useAutoRefresh.js
export const useAutoRefresh = (callback, options = {}) => {
  const {
    interval = 30000, // 30 segundos
    enabled = true,
    onError = null,
    retryAttempts = 3,
    retryDelay = 5000
  } = options;

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  const performRefresh = useCallback(async () => {
    if (!enabled) return;
    
    setIsRefreshing(true);
    setError(null);
    
    try {
      await callback();
      setLastRefresh(new Date());
      setRetryCount(0);
    } catch (err) {
      setError(err);
      onError?.(err);
      
      if (retryCount < retryAttempts) {
        setRetryCount(prev => prev + 1);
        setTimeout(() => performRefresh(), retryDelay);
      }
    } finally {
      setIsRefreshing(false);
    }
  }, [callback, enabled, onError, retryCount, retryAttempts, retryDelay]);

  useEffect(() => {
    if (!enabled) return;

    const intervalId = setInterval(performRefresh, interval);
    return () => clearInterval(intervalId);
  }, [performRefresh, interval, enabled]);

  const manualRefresh = useCallback(() => {
    performRefresh();
  }, [performRefresh]);

  return {
    isRefreshing,
    lastRefresh,
    error,
    retryCount,
    manualRefresh
  };
};
```

## 📊 Estrategias de Monitoreo y Métricas

### Hook de Métricas de Rendimiento
```javascript
// usePerformanceMetrics.js
export const usePerformanceMetrics = () => {
  const [metrics, setMetrics] = useState({
    loadTime: 0,
    renderTime: 0,
    memoryUsage: 0,
    networkRequests: 0
  });

  const measureLoadTime = useCallback(async (operation) => {
    const start = performance.now();
    const result = await operation();
    const end = performance.now();
    
    setMetrics(prev => ({
      ...prev,
      loadTime: end - start
    }));
    
    return result;
  }, []);

  const measureRenderTime = useCallback((componentName) => {
    const start = performance.now();
    
    return () => {
      const end = performance.now();
      setMetrics(prev => ({
        ...prev,
        renderTime: end - start
      }));
    };
  }, []);

  const trackMemoryUsage = useCallback(() => {
    if ('memory' in performance) {
      const memory = performance.memory;
      setMetrics(prev => ({
        ...prev,
        memoryUsage: memory.usedJSHeapSize / 1024 / 1024 // MB
      }));
    }
  }, []);

  return {
    metrics,
    measureLoadTime,
    measureRenderTime,
    trackMemoryUsage
  };
};
```

---

**Documento creado**: $(date)  
**Versión**: 1.0  
**Autor**: Equipo de Desarrollo  
**Estado**: En revisión 