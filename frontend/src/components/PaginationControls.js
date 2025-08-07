import React from 'react';
import './PaginationControls.css';

const PaginationControls = ({ 
  currentPage, 
  totalPages, 
  totalItems, 
  perPage, 
  onPageChange, 
  onPerPageChange,
  hasNext, 
  hasPrev,
  startItem,
  endItem,
  pageNumbers = [],
  showPerPageSelector = true,
  showInfo = true,
  className = ''
}) => {
  if (totalPages <= 1) {
    return null;
  }

  const handlePageClick = (page) => {
    if (page !== currentPage && page >= 1 && page <= totalPages) {
      onPageChange(page);
    }
  };

  const handlePerPageChange = (event) => {
    const newPerPage = parseInt(event.target.value, 10);
    onPerPageChange(newPerPage);
  };

  return (
    <div className={`pagination-controls ${className}`}>
      {/* Información de paginación */}
      {showInfo && (
        <div className="pagination-info">
          <span className="pagination-text">
            Mostrando {startItem}-{endItem} de {totalItems} libros
          </span>
        </div>
      )}

      {/* Controles de navegación */}
      <div className="pagination-navigation">
        {/* Botón Primera Página */}
        <button
          className="pagination-btn pagination-btn-first"
          onClick={() => handlePageClick(1)}
          disabled={!hasPrev}
          title="Primera página"
        >
          <span className="pagination-icon">««</span>
        </button>

        {/* Botón Página Anterior */}
        <button
          className="pagination-btn pagination-btn-prev"
          onClick={() => handlePageClick(currentPage - 1)}
          disabled={!hasPrev}
          title="Página anterior"
        >
          <span className="pagination-icon">‹</span>
        </button>

        {/* Números de página */}
        <div className="pagination-numbers">
          {pageNumbers.map((pageNum) => (
            <button
              key={pageNum}
              className={`pagination-btn pagination-number ${
                pageNum === currentPage ? 'pagination-active' : ''
              }`}
              onClick={() => handlePageClick(pageNum)}
              title={`Página ${pageNum}`}
            >
              {pageNum}
            </button>
          ))}
        </div>

        {/* Botón Página Siguiente */}
        <button
          className="pagination-btn pagination-btn-next"
          onClick={() => handlePageClick(currentPage + 1)}
          disabled={!hasNext}
          title="Página siguiente"
        >
          <span className="pagination-icon">›</span>
        </button>

        {/* Botón Última Página */}
        <button
          className="pagination-btn pagination-btn-last"
          onClick={() => handlePageClick(totalPages)}
          disabled={!hasNext}
          title="Última página"
        >
          <span className="pagination-icon">»»</span>
        </button>
      </div>

      {/* Selector de elementos por página */}
      {showPerPageSelector && (
        <div className="pagination-per-page">
          <label htmlFor="per-page-select" className="per-page-label">
            Por página:
          </label>
          <select
            id="per-page-select"
            value={perPage}
            onChange={handlePerPageChange}
            className="per-page-select"
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>
      )}
    </div>
  );
};

export default PaginationControls; 