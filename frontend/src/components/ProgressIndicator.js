import React, { useState } from 'react';
import './ProgressIndicator.css';

const ProgressIndicator = ({ 
  progress = 0,
  total = 100,
  status = 'loading',
  text = '',
  showPercentage = true,
  showCancel = false,
  onCancel = null,
  variant = 'default',
  size = 'medium',
  className = '',
  animated = true
}) => {
  const [isHovered, setIsHovered] = useState(false);
  
  const percentage = Math.min(100, Math.max(0, (progress / total) * 100));
  
  const getStatusClass = () => {
    switch (status) {
      case 'success':
        return 'progress-indicator--success';
      case 'error':
        return 'progress-indicator--error';
      case 'warning':
        return 'progress-indicator--warning';
      case 'paused':
        return 'progress-indicator--paused';
      default:
        return 'progress-indicator--loading';
    }
  };

  const getVariantClass = () => {
    switch (variant) {
      case 'striped':
        return 'progress-indicator--striped';
      case 'gradient':
        return 'progress-indicator--gradient';
      case 'circular':
        return 'progress-indicator--circular';
      default:
        return 'progress-indicator--default';
    }
  };

  const getSizeClass = () => {
    switch (size) {
      case 'small':
        return 'progress-indicator--small';
      case 'large':
        return 'progress-indicator--large';
      default:
        return 'progress-indicator--medium';
    }
  };

  const getStatusText = () => {
    if (text) return text;
    
    switch (status) {
      case 'success':
        return 'Completado';
      case 'error':
        return 'Error';
      case 'warning':
        return 'Advertencia';
      case 'paused':
        return 'Pausado';
      default:
        return 'Procesando...';
    }
  };

  const handleCancel = () => {
    if (onCancel && typeof onCancel === 'function') {
      onCancel();
    }
  };

  // Variante circular
  if (variant === 'circular') {
    const radius = size === 'small' ? 20 : size === 'large' ? 40 : 30;
    const circumference = 2 * Math.PI * radius;
    const strokeDasharray = circumference;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;

    return (
      <div className={`progress-indicator progress-indicator--circular ${getStatusClass()} ${getSizeClass()} ${className}`}>
        <div className="progress-indicator__circular">
          <svg
            className="progress-indicator__circular-svg"
            width={radius * 2 + 10}
            height={radius * 2 + 10}
            viewBox={`0 0 ${radius * 2 + 10} ${radius * 2 + 10}`}
          >
            {/* Fondo */}
            <circle
              className="progress-indicator__circular-bg"
              cx={radius + 5}
              cy={radius + 5}
              r={radius}
              strokeWidth="3"
            />
            {/* Progreso */}
            <circle
              className={`progress-indicator__circular-progress ${animated ? 'progress-indicator__circular-progress--animated' : ''}`}
              cx={radius + 5}
              cy={radius + 5}
              r={radius}
              strokeWidth="3"
              strokeDasharray={strokeDasharray}
              strokeDashoffset={strokeDashoffset}
              transform={`rotate(-90 ${radius + 5} ${radius + 5})`}
            />
          </svg>
          <div className="progress-indicator__circular-content">
            {showPercentage && (
              <div className="progress-indicator__circular-percentage">
                {Math.round(percentage)}%
              </div>
            )}
            <div className="progress-indicator__circular-text">
              {getStatusText()}
            </div>
          </div>
        </div>
        {showCancel && onCancel && (
          <button
            className="progress-indicator__cancel-btn"
            onClick={handleCancel}
            type="button"
            aria-label="Cancelar operación"
          >
            ✕
          </button>
        )}
      </div>
    );
  }

  // Variantes lineales
  return (
    <div 
      className={`progress-indicator ${getStatusClass()} ${getVariantClass()} ${getSizeClass()} ${className}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="progress-indicator__header">
        <div className="progress-indicator__text">
          {getStatusText()}
        </div>
        {showPercentage && (
          <div className="progress-indicator__percentage">
            {Math.round(percentage)}%
          </div>
        )}
      </div>
      
      <div className="progress-indicator__bar-container">
        <div className="progress-indicator__bar">
          <div 
            className={`progress-indicator__bar-fill ${animated ? 'progress-indicator__bar-fill--animated' : ''}`}
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
        
        {showCancel && onCancel && (
          <button
            className={`progress-indicator__cancel-btn ${isHovered ? 'progress-indicator__cancel-btn--visible' : ''}`}
            onClick={handleCancel}
            type="button"
            aria-label="Cancelar operación"
          >
            ✕
          </button>
        )}
      </div>
      
      {progress !== undefined && total !== undefined && (
        <div className="progress-indicator__details">
          {progress} de {total}
        </div>
      )}
    </div>
  );
};

// Componente para múltiples progresos
export const MultiProgressIndicator = ({ 
  items = [],
  className = '',
  showCancel = false,
  onCancel = null
}) => {
  return (
    <div className={`multi-progress-indicator ${className}`}>
      {items.map((item, index) => (
        <ProgressIndicator
          key={index}
          progress={item.progress}
          total={item.total}
          status={item.status}
          text={item.text}
          showPercentage={item.showPercentage !== false}
          showCancel={showCancel}
          onCancel={onCancel ? () => onCancel(index) : null}
          variant={item.variant}
          size={item.size}
          animated={item.animated !== false}
        />
      ))}
    </div>
  );
};

// Componente para progreso indeterminado
export const IndeterminateProgress = ({ 
  status = 'loading',
  text = 'Procesando...',
  variant = 'default',
  size = 'medium',
  className = ''
}) => {
  return (
    <div className={`indeterminate-progress indeterminate-progress--${variant} indeterminate-progress--${size} ${className}`}>
      <div className="indeterminate-progress__bar">
        <div className="indeterminate-progress__bar-fill"></div>
      </div>
      {text && (
        <div className="indeterminate-progress__text">
          {text}
        </div>
      )}
    </div>
  );
};

export default ProgressIndicator; 