import React from 'react';
import './Card.css';

const Card = ({ 
  children, 
  variant = 'default', 
  size = 'medium', 
  hoverable = false, 
  interactive = false,
  className = '',
  onClick,
  ...props 
}) => {
  const baseClass = 'modern-card';
  const variantClass = `modern-card--${variant}`;
  const sizeClass = `modern-card--${size}`;
  const hoverableClass = hoverable ? 'modern-card--hoverable' : '';
  const interactiveClass = interactive ? 'modern-card--interactive' : '';
  
  const cardClass = [
    baseClass,
    variantClass,
    sizeClass,
    hoverableClass,
    interactiveClass,
    className
  ].filter(Boolean).join(' ');

  const handleClick = (e) => {
    if (interactive && onClick) {
      onClick(e);
    }
  };

  return (
    <div
      className={cardClass}
      onClick={handleClick}
      role={interactive ? 'button' : undefined}
      tabIndex={interactive ? 0 : undefined}
      {...props}
    >
      {children}
    </div>
  );
};

// Componentes de tarjeta especializados
Card.Header = ({ children, className = '', ...props }) => (
  <div className={`modern-card__header ${className}`} {...props}>
    {children}
  </div>
);

Card.Body = ({ children, className = '', ...props }) => (
  <div className={`modern-card__body ${className}`} {...props}>
    {children}
  </div>
);

Card.Footer = ({ children, className = '', ...props }) => (
  <div className={`modern-card__footer ${className}`} {...props}>
    {children}
  </div>
);

Card.Image = ({ src, alt, className = '', ...props }) => (
  <div className={`modern-card__image ${className}`} {...props}>
    <img src={src} alt={alt} />
  </div>
);

Card.Title = ({ children, className = '', ...props }) => (
  <h3 className={`modern-card__title ${className}`} {...props}>
    {children}
  </h3>
);

Card.Subtitle = ({ children, className = '', ...props }) => (
  <p className={`modern-card__subtitle ${className}`} {...props}>
    {children}
  </p>
);

Card.Content = ({ children, className = '', ...props }) => (
  <div className={`modern-card__content ${className}`} {...props}>
    {children}
  </div>
);

Card.Actions = ({ children, className = '', ...props }) => (
  <div className={`modern-card__actions ${className}`} {...props}>
    {children}
  </div>
);

export default Card; 