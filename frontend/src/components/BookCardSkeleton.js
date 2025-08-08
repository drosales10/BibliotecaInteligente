import React from 'react';
import './BookCardSkeleton.css';

const BookCardSkeleton = ({ 
  variant = 'default', 
  className = '', 
  showTitle = true, 
  showAuthor = true,
  showCategory = true 
}) => {
  const getVariantClass = () => {
    switch (variant) {
      case 'compact':
        return 'book-card-skeleton--compact';
      case 'detailed':
        return 'book-card-skeleton--detailed';
      default:
        return 'book-card-skeleton--default';
    }
  };

  return (
    <div className={`book-card-skeleton ${getVariantClass()} ${className}`}>
      {/* Skeleton de la portada */}
      <div className="book-card-skeleton__cover">
        <div className="book-card-skeleton__cover-placeholder"></div>
      </div>
      
      {/* Skeleton del contenido */}
      <div className="book-card-skeleton__content">
        {showTitle && (
          <div className="book-card-skeleton__title">
            <div className="book-card-skeleton__line book-card-skeleton__line--title"></div>
            <div className="book-card-skeleton__line book-card-skeleton__line--title-short"></div>
          </div>
        )}
        
        {showAuthor && (
          <div className="book-card-skeleton__author">
            <div className="book-card-skeleton__line book-card-skeleton__line--author"></div>
          </div>
        )}
        
        {showCategory && (
          <div className="book-card-skeleton__category">
            <div className="book-card-skeleton__line book-card-skeleton__line--category"></div>
          </div>
        )}
        
        {/* Skeleton de botones de acción */}
        <div className="book-card-skeleton__actions">
          <div className="book-card-skeleton__button book-card-skeleton__button--primary"></div>
          <div className="book-card-skeleton__button book-card-skeleton__button--secondary"></div>
        </div>
      </div>
    </div>
  );
};

// Componente para mostrar múltiples skeletons
export const BookCardSkeletonGrid = ({ 
  count = 6, 
  variant = 'default',
  className = '',
  showTitle = true,
  showAuthor = true,
  showCategory = true
}) => {
  return (
    <div className={`book-card-skeleton-grid ${className}`}>
      {Array.from({ length: count }, (_, index) => (
        <BookCardSkeleton
          key={index}
          variant={variant}
          showTitle={showTitle}
          showAuthor={showAuthor}
          showCategory={showCategory}
        />
      ))}
    </div>
  );
};

export default BookCardSkeleton; 