import { useState, useCallback, useMemo } from 'react';

export const usePagination = (initialPage = 1, initialPerPage = 20) => {
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [perPage, setPerPage] = useState(initialPerPage);
  const [totalItems, setTotalItems] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  const updatePaginationInfo = useCallback((paginationData) => {
    if (paginationData) {
      setTotalItems(paginationData.total || 0);
      setTotalPages(paginationData.total_pages || 0);
      setCurrentPage(paginationData.page || 1);
      setPerPage(paginationData.per_page || initialPerPage);
    }
  }, [initialPerPage]);

  const goToPage = useCallback((page) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
  }, [totalPages]);

  const goToNextPage = useCallback(() => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  }, [currentPage, totalPages]);

  const goToPrevPage = useCallback(() => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  }, [currentPage]);

  const goToFirstPage = useCallback(() => {
    setCurrentPage(1);
  }, []);

  const goToLastPage = useCallback(() => {
    setCurrentPage(totalPages);
  }, [totalPages]);

  const changePerPage = useCallback((newPerPage) => {
    setPerPage(newPerPage);
    setCurrentPage(1); // Reset a la primera página cuando cambia el tamaño
  }, []);

  const resetPagination = useCallback(() => {
    setCurrentPage(initialPage);
    setPerPage(initialPerPage);
    setTotalItems(0);
    setTotalPages(0);
  }, [initialPage, initialPerPage]);

  const paginationInfo = useMemo(() => ({
    currentPage,
    perPage,
    totalItems,
    totalPages,
    hasNext: currentPage < totalPages,
    hasPrev: currentPage > 1,
    startItem: (currentPage - 1) * perPage + 1,
    endItem: Math.min(currentPage * perPage, totalItems),
    pageNumbers: generatePageNumbers(currentPage, totalPages)
  }), [currentPage, perPage, totalItems, totalPages]);

  return {
    // Estado
    currentPage,
    perPage,
    totalItems,
    totalPages,
    
    // Información calculada
    paginationInfo,
    
    // Acciones
    goToPage,
    goToNextPage,
    goToPrevPage,
    goToFirstPage,
    goToLastPage,
    changePerPage,
    updatePaginationInfo,
    resetPagination,
    
    // Setters directos
    setCurrentPage,
    setPerPage,
    setTotalItems,
    setTotalPages
  };
};

// Función auxiliar para generar números de página
function generatePageNumbers(currentPage, totalPages, maxVisible = 5) {
  if (totalPages <= maxVisible) {
    return Array.from({ length: totalPages }, (_, i) => i + 1);
  }

  const halfVisible = Math.floor(maxVisible / 2);
  let start = Math.max(1, currentPage - halfVisible);
  let end = Math.min(totalPages, start + maxVisible - 1);

  // Ajustar si estamos cerca del final
  if (end === totalPages) {
    start = Math.max(1, end - maxVisible + 1);
  }

  const pages = [];
  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  return pages;
} 