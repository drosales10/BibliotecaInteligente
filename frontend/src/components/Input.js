import React, { forwardRef } from 'react';
import './Input.css';

const Input = forwardRef(({ 
  type = 'text',
  label,
  placeholder,
  value,
  onChange,
  onFocus,
  onBlur,
  error,
  success,
  disabled = false,
  required = false,
  fullWidth = false,
  size = 'medium',
  variant = 'default',
  icon,
  iconPosition = 'left',
  className = '',
  ...props 
}, ref) => {
  const baseClass = 'modern-input';
  const variantClass = `modern-input--${variant}`;
  const sizeClass = `modern-input--${size}`;
  const widthClass = fullWidth ? 'modern-input--full-width' : '';
  const errorClass = error ? 'modern-input--error' : '';
  const successClass = success ? 'modern-input--success' : '';
  const disabledClass = disabled ? 'modern-input--disabled' : '';
  const iconClass = icon ? `modern-input--with-icon modern-input--icon-${iconPosition}` : '';
  
  const inputClass = [
    baseClass,
    variantClass,
    sizeClass,
    widthClass,
    errorClass,
    successClass,
    disabledClass,
    iconClass,
    className
  ].filter(Boolean).join(' ');

  const containerClass = `modern-input-container ${fullWidth ? 'modern-input-container--full-width' : ''}`;

  return (
    <div className={containerClass}>
      {label && (
        <label className="modern-input__label">
          {label}
          {required && <span className="modern-input__required">*</span>}
        </label>
      )}
      
      <div className="modern-input__wrapper">
        {icon && iconPosition === 'left' && (
          <span className="modern-input__icon modern-input__icon--left">
            {icon}
          </span>
        )}
        
        <input
          ref={ref}
          type={type}
          className={inputClass}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          onFocus={onFocus}
          onBlur={onBlur}
          disabled={disabled}
          required={required}
          {...props}
        />
        
        {icon && iconPosition === 'right' && (
          <span className="modern-input__icon modern-input__icon--right">
            {icon}
          </span>
        )}
        
        {/* Indicadores de estado */}
        {success && (
          <span className="modern-input__indicator modern-input__indicator--success">
            ✓
          </span>
        )}
        
        {error && (
          <span className="modern-input__indicator modern-input__indicator--error">
            ✕
          </span>
        )}
      </div>
      
      {error && (
        <div className="modern-input__error">
          {error}
        </div>
      )}
      
      {success && !error && (
        <div className="modern-input__success">
          {success}
        </div>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input; 