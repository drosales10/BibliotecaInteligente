import { useEffect, useRef, useState, useCallback } from 'react';

export const useIntersectionObserver = (options = {}) => {
  const [isIntersecting, setIsIntersecting] = useState(false);
  const [hasIntersected, setHasIntersected] = useState(false);
  const elementRef = useRef(null);

  const {
    threshold = 0.1,
    rootMargin = '50px',
    root = null,
    triggerOnce = true
  } = options;

  const handleIntersection = useCallback((entries) => {
    const [entry] = entries;
    
    if (entry.isIntersecting) {
      setIsIntersecting(true);
      if (triggerOnce) {
        setHasIntersected(true);
      }
    } else if (!triggerOnce) {
      setIsIntersecting(false);
    }
  }, [triggerOnce]);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const observer = new IntersectionObserver(handleIntersection, {
      threshold,
      rootMargin,
      root
    });

    observer.observe(element);

    return () => {
      observer.unobserve(element);
    };
  }, [handleIntersection, threshold, rootMargin, root]);

  const reset = useCallback(() => {
    setIsIntersecting(false);
    setHasIntersected(false);
  }, []);

  return {
    elementRef,
    isIntersecting,
    hasIntersected,
    reset
  };
};

// Hook específico para lazy loading de imágenes
export const useLazyImage = (src, options = {}) => {
  const [imageSrc, setImageSrc] = useState(null);
  const [imageLoading, setImageLoading] = useState(false);
  const [imageError, setImageError] = useState(false);
  
  const {
    threshold = 0.1,
    rootMargin = '100px',
    placeholder = null,
    fallback = null
  } = options;

  const { elementRef, isIntersecting, hasIntersected } = useIntersectionObserver({
    threshold,
    rootMargin,
    triggerOnce: true
  });

  useEffect(() => {
    if (!src || !hasIntersected) {
      setImageSrc(placeholder);
      return;
    }

    setImageLoading(true);
    setImageError(false);

    const img = new Image();
    
    img.onload = () => {
      setImageSrc(src);
      setImageLoading(false);
    };

    img.onerror = () => {
      setImageSrc(fallback || placeholder);
      setImageLoading(false);
      setImageError(true);
    };

    img.src = src;

    return () => {
      img.onload = null;
      img.onerror = null;
    };
  }, [src, hasIntersected, placeholder, fallback]);

  return {
    elementRef,
    imageSrc,
    imageLoading,
    imageError,
    isIntersecting,
    hasIntersected
  };
}; 