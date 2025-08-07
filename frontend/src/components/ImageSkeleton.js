import React from 'react';
import './ImageSkeleton.css';

const ImageSkeleton = ({ 
  width = '100%', 
  height = '200px', 
  className = '',
  variant = 'default', // 'default', 'book-cover', 'avatar', 'card'
  animated = true,
  borderRadius = '8px',
  ...props 
}) => {
  const getSkeletonClass = () => {
    const baseClass = 'image-skeleton';
    const variantClass = `image-skeleton--${variant}`;
    const animationClass = animated ? 'image-skeleton--animated' : '';
    return `${baseClass} ${variantClass} ${animationClass} ${className}`.trim();
  };

  const getSkeletonStyle = () => ({
    width,
    height,
    borderRadius,
    ...props.style
  });

  return (
    <div 
      className={getSkeletonClass()}
      style={getSkeletonStyle()}
      {...props}
    >
      {variant === 'book-cover' && (
        <div className="book-cover-skeleton">
          <div className="book-cover-placeholder">
            <span className="book-icon">📚</span>
          </div>
        </div>
      )}
      {variant === 'avatar' && (
        <div className="avatar-skeleton">
          <div className="avatar-placeholder">
            <span className="avatar-icon">👤</span>
          </div>
        </div>
      )}
      {variant === 'card' && (
        <div className="card-skeleton">
          <div className="card-image-placeholder"></div>
          <div className="card-content-placeholder">
            <div className="card-title-placeholder"></div>
            <div className="card-subtitle-placeholder"></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ImageSkeleton; 