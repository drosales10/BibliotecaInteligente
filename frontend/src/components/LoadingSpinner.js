import React from 'react';
import './LoadingSpinner.css';

const LoadingSpinner = ({ 
  size = 'medium',
  color = 'primary',
  variant = 'spinner',
  text = '',
  className = '',
  showText = true
}) => {
  const getSizeClass = () => {
    switch (size) {
      case 'small':
        return 'loading-spinner--small';
      case 'large':
        return 'loading-spinner--large';
      case 'xlarge':
        return 'loading-spinner--xlarge';
      default:
        return 'loading-spinner--medium';
    }
  };

  const getColorClass = () => {
    switch (color) {
      case 'secondary':
        return 'loading-spinner--secondary';
      case 'success':
        return 'loading-spinner--success';
      case 'warning':
        return 'loading-spinner--warning';
      case 'error':
        return 'loading-spinner--error';
      case 'light':
        return 'loading-spinner--light';
      default:
        return 'loading-spinner--primary';
    }
  };

  const getVariantClass = () => {
    switch (variant) {
      case 'dots':
        return 'loading-spinner--dots';
      case 'pulse':
        return 'loading-spinner--pulse';
      case 'bars':
        return 'loading-spinner--bars';
      case 'ring':
        return 'loading-spinner--ring';
      default:
        return 'loading-spinner--spinner';
    }
  };

  const renderSpinner = () => {
    switch (variant) {
      case 'dots':
        return (
          <div className="loading-spinner__dots">
            <div className="loading-spinner__dot"></div>
            <div className="loading-spinner__dot"></div>
            <div className="loading-spinner__dot"></div>
          </div>
        );
      
      case 'pulse':
        return (
          <div className="loading-spinner__pulse"></div>
        );
      
      case 'bars':
        return (
          <div className="loading-spinner__bars">
            <div className="loading-spinner__bar"></div>
            <div className="loading-spinner__bar"></div>
            <div className="loading-spinner__bar"></div>
            <div className="loading-spinner__bar"></div>
            <div className="loading-spinner__bar"></div>
          </div>
        );
      
      case 'ring':
        return (
          <div className="loading-spinner__ring">
            <div></div>
            <div></div>
            <div></div>
            <div></div>
          </div>
        );
      
      default:
        return (
          <div className="loading-spinner__spinner">
            <div className="loading-spinner__spinner-inner"></div>
          </div>
        );
    }
  };

  return (
    <div className={`loading-spinner ${getSizeClass()} ${getColorClass()} ${getVariantClass()} ${className}`}>
      {renderSpinner()}
      {showText && text && (
        <div className="loading-spinner__text">
          {text}
        </div>
      )}
    </div>
  );
};

// Componente para loading overlay
export const LoadingOverlay = ({ 
  isLoading = false,
  text = 'Cargando...',
  size = 'large',
  variant = 'spinner',
  className = '',
  children
}) => {
  if (!isLoading) {
    return children;
  }

  return (
    <div className={`loading-overlay ${className}`}>
      <div className="loading-overlay__content">
        <LoadingSpinner 
          size={size}
          variant={variant}
          text={text}
          showText={true}
        />
      </div>
      {children && (
        <div className="loading-overlay__children">
          {children}
        </div>
      )}
    </div>
  );
};

// Componente para loading inline
export const LoadingInline = ({ 
  isLoading = false,
  text = 'Cargando...',
  size = 'small',
  variant = 'dots',
  className = '',
  children
}) => {
  if (!isLoading) {
    return children;
  }

  return (
    <div className={`loading-inline ${className}`}>
      <LoadingSpinner 
        size={size}
        variant={variant}
        text={text}
        showText={true}
      />
    </div>
  );
};

export default LoadingSpinner; 