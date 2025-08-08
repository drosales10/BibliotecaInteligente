import React from 'react';
import { useLazyImage } from '../hooks/useIntersectionObserver';
import ImageSkeleton from './ImageSkeleton';
import './LazyImage.css';

const LazyImage = ({ 
  src, 
  alt, 
  title,
  className = '',
  placeholder = null,
  fallback = null,
  threshold = 0.1,
  rootMargin = '100px',
  showSkeleton = true,
  skeletonProps = {},
  onLoad,
  onError,
  ...props 
}) => {
  const {
    elementRef,
    imageSrc,
    imageLoading,
    imageError,
    hasIntersected
  } = useLazyImage(src, {
    threshold,
    rootMargin,
    placeholder,
    fallback
  });

  const handleImageLoad = (event) => {
    if (onLoad) {
      onLoad(event);
    }
  };

  const handleImageError = (event) => {
    if (onError) {
      onError(event);
    }
  };

  // Si no hay imagen y no ha intersectado, mostrar skeleton
  if (!hasIntersected && showSkeleton) {
    return (
      <div ref={elementRef} className={`lazy-image-container ${className}`}>
        <ImageSkeleton {...skeletonProps} />
      </div>
    );
  }

  // Si está cargando y queremos mostrar skeleton
  if (imageLoading && showSkeleton) {
    return (
      <div className={`lazy-image-container ${className}`}>
        <ImageSkeleton {...skeletonProps} />
      </div>
    );
  }

  // Si hay error y no hay fallback, mostrar skeleton o placeholder
  if (imageError && !fallback) {
    if (showSkeleton) {
      return (
        <div className={`lazy-image-container ${className}`}>
          <ImageSkeleton {...skeletonProps} />
        </div>
      );
    }
    return (
      <div className={`lazy-image-container ${className}`}>
        <div className="image-error-placeholder">
          <span className="error-icon">⚠️</span>
          <span className="error-text">Error</span>
        </div>
      </div>
    );
  }

  // Si no hay src válido, mostrar placeholder o skeleton
  if (!imageSrc) {
    if (showSkeleton) {
      return (
        <div ref={elementRef} className={`lazy-image-container ${className}`}>
          <ImageSkeleton {...skeletonProps} />
        </div>
      );
    }
    return (
      <div ref={elementRef} className={`lazy-image-container ${className}`}>
        <div className="image-placeholder">
          <span className="placeholder-icon">📷</span>
        </div>
      </div>
    );
  }

  // Renderizar la imagen
  return (
    <div ref={elementRef} className={`lazy-image-container ${className}`}>
      <img
        src={imageSrc}
        alt={alt}
        title={title}
        className={`lazy-image ${imageLoading ? 'loading' : ''} ${imageError ? 'error' : ''}`}
        onLoad={handleImageLoad}
        onError={handleImageError}
        {...props}
      />
      {imageLoading && showSkeleton && (
        <div className="lazy-image-overlay">
          <ImageSkeleton {...skeletonProps} />
        </div>
      )}
    </div>
  );
};

export default LazyImage; 