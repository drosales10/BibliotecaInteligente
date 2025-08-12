import { useState, useCallback, useRef } from 'react';

const useLoadingState = (initialStates = {}) => {
  const [loadingStates, setLoadingStates] = useState(initialStates);
  const loadingStatesRef = useRef(initialStates); // Ref para acceso inmediato
  const loadingTimeouts = useRef(new Map());
  const stopLoadingRef = useRef();

  // Obtener estado de carga para una operación específica
  const isLoading = useCallback((operation) => {
    return loadingStates[operation] || false;
  }, [loadingStates]);

  // Obtener todos los estados de carga
  const getAllLoadingStates = useCallback(() => {
    return loadingStates;
  }, [loadingStates]);

  // Verificar si alguna operación está cargando
  const isAnyLoading = useCallback(() => {
    return Object.values(loadingStates).some(state => state);
  }, [loadingStates]);

  // Verificar si múltiples operaciones están cargando
  const areLoading = useCallback((operations) => {
    return operations.every(operation => loadingStates[operation]);
  }, [loadingStates]);

    // Detener carga para una operación
  const stopLoading = useCallback((operation) => {
    setLoadingStates(prev => {
      const newState = {
        ...prev,
        [operation]: false
      };
      loadingStatesRef.current = newState; // Sincronizar ref
      return newState;
    });
    
    // Limpiar timeout si existe
    const timeoutId = loadingTimeouts.current.get(operation);
    if (timeoutId) {
      clearTimeout(timeoutId);
      loadingTimeouts.current.delete(operation);
    }
  }, []);

  // Asignar la función a la ref para que esté disponible
  stopLoadingRef.current = stopLoading;

  // Iniciar carga para una operación
  const startLoading = useCallback((operation, timeout = null) => {
    setLoadingStates(prev => {
      const newState = {
        ...prev,
        [operation]: true
      };
      loadingStatesRef.current = newState; // Sincronizar ref
      return newState;
    });

    // Configurar timeout si se especifica
    if (timeout && typeof timeout === 'number') {
      const timeoutId = setTimeout(() => {
        stopLoadingRef.current(operation);
      }, timeout);
      loadingTimeouts.current.set(operation, timeoutId);
    }
  }, []);

  // Iniciar múltiples operaciones
  const startMultipleLoading = useCallback((operations, timeout = null) => {
    const newStates = {};
    operations.forEach(operation => {
      newStates[operation] = true;
    });

    setLoadingStates(prev => ({
      ...prev,
      ...newStates
    }));

    // Configurar timeout para todas las operaciones
    if (timeout && typeof timeout === 'number') {
      operations.forEach(operation => {
        const timeoutId = setTimeout(() => {
          stopLoadingRef.current(operation);
        }, timeout);
        loadingTimeouts.current.set(operation, timeoutId);
      });
    }
  }, []);

  // Detener múltiples operaciones
  const stopMultipleLoading = useCallback((operations) => {
    const newStates = {};
    operations.forEach(operation => {
      newStates[operation] = false;
      // Limpiar timeout si existe
      const timeoutId = loadingTimeouts.current.get(operation);
      if (timeoutId) {
        clearTimeout(timeoutId);
        loadingTimeouts.current.delete(operation);
      }
    });

    setLoadingStates(prev => ({
      ...prev,
      ...newStates
    }));
  }, []);

  // Detener todas las operaciones
  const stopAllLoading = useCallback(() => {
    setLoadingStates({});
    
    // Limpiar todos los timeouts
    loadingTimeouts.current.forEach(timeoutId => {
      clearTimeout(timeoutId);
    });
    loadingTimeouts.current.clear();
  }, []);

  // Wrapper para operaciones asíncronas - optimizado
  const withLoading = useCallback(async (operation, asyncFunction, timeout = null) => {
    // Usar una ref para verificar estado actual sin dependencias
    if (loadingStatesRef.current[operation]) {
      console.warn(`Operación ${operation} ya está en curso, ignorando llamada duplicada`);
      return;
    }

    try {
      startLoading(operation, timeout);
      const result = await asyncFunction();
      return result;
    } finally {
      console.log(`🏁 withLoading terminando operación: ${operation}`);
      stopLoading(operation);
    }
  }, [startLoading, stopLoading]); // Incluir stopLoading como dependencia

  // Wrapper para múltiples operaciones asíncronas
  const withMultipleLoading = useCallback(async (operations, asyncFunctions, timeout = null) => {
    // Verificar que ninguna operación esté ya en curso
    const alreadyLoading = operations.filter(op => loadingStates[op]);
    if (alreadyLoading.length > 0) {
      console.warn(`Operaciones ya en curso: ${alreadyLoading.join(', ')}, ignorando llamada duplicada`);
      return;
    }

    try {
      startMultipleLoading(operations, timeout);
      const results = await Promise.all(asyncFunctions);
      return results;
    } finally {
      stopMultipleLoading(operations);
    }
  }, [startLoading, stopMultipleLoading, loadingStates]);

  // Obtener operaciones que están cargando
  const getLoadingOperations = useCallback(() => {
    return Object.entries(loadingStates)
      .filter(([_, isLoading]) => isLoading)
      .map(([operation]) => operation);
  }, [loadingStates]);

  // Obtener operaciones que no están cargando
  const getNonLoadingOperations = useCallback(() => {
    return Object.entries(loadingStates)
      .filter(([_, isLoading]) => !isLoading)
      .map(([operation]) => operation);
  }, [loadingStates]);

  // Contar operaciones en carga
  const getLoadingCount = useCallback(() => {
    return Object.values(loadingStates).filter(Boolean).length;
  }, [loadingStates]);

  // Verificar si una operación específica no está cargando
  const isNotLoading = useCallback((operation) => {
    return !loadingStates[operation];
  }, [loadingStates]);

  // Resetear estados de carga
  const resetLoadingStates = useCallback((newStates = {}) => {
    // Limpiar todos los timeouts existentes
    loadingTimeouts.current.forEach(timeoutId => {
      clearTimeout(timeoutId);
    });
    loadingTimeouts.current.clear();

    setLoadingStates(newStates);
  }, []);

  // Actualizar estado de carga específico
  const updateLoadingState = useCallback((operation, isLoading) => {
    setLoadingStates(prev => ({
      ...prev,
      [operation]: isLoading
    }));

    // Limpiar timeout si se detiene la carga
    if (!isLoading) {
      const timeoutId = loadingTimeouts.current.get(operation);
      if (timeoutId) {
        clearTimeout(timeoutId);
        loadingTimeouts.current.delete(operation);
      }
    }
  }, []);

  // Limpiar timeouts al desmontar
  const cleanup = useCallback(() => {
    loadingTimeouts.current.forEach(timeoutId => {
      clearTimeout(timeoutId);
    });
    loadingTimeouts.current.clear();
  }, []);

  return {
    // Estados
    loadingStates,
    isLoading,
    isNotLoading,
    isAnyLoading,
    areLoading,
    getAllLoadingStates,
    getLoadingOperations,
    getNonLoadingOperations,
    getLoadingCount,

    // Métodos de control
    startLoading,
    stopLoading,
    startMultipleLoading,
    stopMultipleLoading,
    stopAllLoading,
    updateLoadingState,
    resetLoadingStates,

    // Wrappers para operaciones asíncronas
    withLoading,
    withMultipleLoading,

    // Limpieza
    cleanup
  };
};

export default useLoadingState; 