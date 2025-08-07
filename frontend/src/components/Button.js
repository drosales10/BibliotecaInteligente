import React from 'react';
import './Button.css';

const Button = ({ 
  children, 
  variant = 'primary', 
  size = 'medium', 
  disabled = false, 
  loading = false,
  icon,
  iconPosition = 'left',
  fullWidth = false,
  className = '',
  onClick,
  type = 'button',
  ...props 
}) => {
  const baseClass = 'modern-button';
  const variantClass = `modern-button--${variant}`;
  const sizeClass = `modern-button--${size}`;
  const widthClass = fullWidth ? 'modern-button--full-width' : '';
  const loadingClass = loading ? 'modern-button--loading' : '';
  const disabledClass = disabled ? 'modern-button--disabled' : '';
  
  const buttonClass = [
    baseClass,
    variantClass,
    sizeClass,
    widthClass,
    loadingClass,
    disabledClass,
    className
  ].filter(Boolean).join(' ');

  const handleClick = (e) => {
    if (!disabled && !loading && onClick) {
      onClick(e);
    }
  };

  return (
    <button
      type={type}
      className={buttonClass}
      onClick={handleClick}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <span className="modern-button__loader">
          <svg className="modern-button__spinner" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeDasharray="31.416" strokeDashoffset="31.416">
              <animate attributeName="stroke-dasharray" dur="2s" values="0 31.416;15.708 15.708;0 31.416" repeatCount="indefinite" />
              <animate attributeName="stroke-dashoffset" dur="2s" values="0;-15.708;-31.416" repeatCount="indefinite" />
            </circle>
          </svg>
        </span>
      )}
      
      {!loading && icon && iconPosition === 'left' && (
        <span className="modern-button__icon modern-button__icon--left">
          {icon}
        </span>
      )}
      
      <span className="modern-button__content">
        {children}
      </span>
      
      {!loading && icon && iconPosition === 'right' && (
        <span className="modern-button__icon modern-button__icon--right">
          {icon}
        </span>
      )}
    </button>
  );
};

export default Button; 