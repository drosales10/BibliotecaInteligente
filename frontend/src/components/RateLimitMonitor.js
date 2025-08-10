import React, { useState, useEffect } from 'react';
import { getBackendUrl } from '../config/api';
import './RateLimitMonitor.css';

const RateLimitMonitor = ({ isOpen, onClose }) => {
  const [rateLimitStats, setRateLimitStats] = useState(null);
  const [queueStats, setQueueStats] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    if (isOpen) {
      fetchStats();
    }
  }, [isOpen]);

  useEffect(() => {
    let interval;
    if (isOpen && autoRefresh) {
      interval = setInterval(fetchStats, 5000); // Actualizar cada 5 segundos
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isOpen, autoRefresh]);

  const fetchStats = async () => {
    setIsLoading(true);
    try {
      const apiUrl = getBackendUrl();
      
      // Obtener estadísticas de rate limiting
      const rateLimitResponse = await fetch(`${apiUrl}/api/rate-limit-stats`);
      if (rateLimitResponse.ok) {
        const rateLimitData = await rateLimitResponse.json();
        setRateLimitStats(rateLimitData.rate_limit_stats);
      }
      
      // Obtener estadísticas de cola RAG
      const queueResponse = await fetch(`${apiUrl}/api/rag-queue/stats`);
      if (queueResponse.ok) {
        const queueData = await queueResponse.json();
        setQueueStats(queueData.queue_stats);
      }
    } catch (error) {
      console.error('Error obteniendo estadísticas:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (seconds) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  };

  const getHealthColor = (successRate) => {
    if (successRate >= 95) return 'success';
    if (successRate >= 80) return 'warning';
    return 'error';
  };

  if (!isOpen) return null;

  return (
    <div className="rate-limit-monitor-overlay" onClick={onClose}>
      <div className="rate-limit-monitor" onClick={(e) => e.stopPropagation()}>
        <div className="monitor-header">
          <h2>🚦 Monitor de Rate Limiting</h2>
          <div className="monitor-controls">
            <label className="auto-refresh-toggle">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
              Auto-actualizar
            </label>
            <button onClick={fetchStats} disabled={isLoading} className="refresh-btn">
              {isLoading ? '🔄' : '↻'} Actualizar
            </button>
            <button onClick={onClose} className="close-btn">✕</button>
          </div>
        </div>

        <div className="monitor-content">
          {/* Estadísticas de Rate Limiting */}
          <div className="stats-section">
            <h3>📊 Rate Limiting - Gemini API</h3>
            {rateLimitStats ? (
              <div className="rate-limit-grid">
                {/* Análisis General */}
                {rateLimitStats.gemini_analysis && (
                  <div className="rate-limit-card">
                    <h4>🧠 Análisis de Libros</h4>
                    <div className="stat-grid">
                      <div className="stat-item">
                        <span className="stat-label">Llamadas/minuto:</span>
                        <span className="stat-value">
                          {rateLimitStats.gemini_analysis.current_usage.calls_this_minute} / {rateLimitStats.gemini_analysis.config.max_per_minute}
                        </span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Llamadas/hora:</span>
                        <span className="stat-value">
                          {rateLimitStats.gemini_analysis.current_usage.calls_this_hour} / {rateLimitStats.gemini_analysis.config.max_per_hour}
                        </span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Concurrentes:</span>
                        <span className="stat-value">
                          {rateLimitStats.gemini_analysis.current_usage.concurrent_calls} / {rateLimitStats.gemini_analysis.config.max_concurrent}
                        </span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Éxito:</span>
                        <span className={`stat-value ${getHealthColor(rateLimitStats.gemini_analysis.statistics.success_rate)}`}>
                          {rateLimitStats.gemini_analysis.statistics.success_rate.toFixed(1)}%
                        </span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Tiempo promedio:</span>
                        <span className="stat-value">
                          {formatTime(rateLimitStats.gemini_analysis.statistics.average_response_time)}
                        </span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Rate limited:</span>
                        <span className="stat-value error">
                          {rateLimitStats.gemini_analysis.statistics.rate_limited_calls}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Embeddings */}
                {rateLimitStats.gemini_embeddings && (
                  <div className="rate-limit-card">
                    <h4>🔗 Embeddings RAG</h4>
                    <div className="stat-grid">
                      <div className="stat-item">
                        <span className="stat-label">Llamadas/minuto:</span>
                        <span className="stat-value">
                          {rateLimitStats.gemini_embeddings.current_usage.calls_this_minute} / {rateLimitStats.gemini_embeddings.config.max_per_minute}
                        </span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Llamadas/hora:</span>
                        <span className="stat-value">
                          {rateLimitStats.gemini_embeddings.current_usage.calls_this_hour} / {rateLimitStats.gemini_embeddings.config.max_per_hour}
                        </span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Concurrentes:</span>
                        <span className="stat-value">
                          {rateLimitStats.gemini_embeddings.current_usage.concurrent_calls} / {rateLimitStats.gemini_embeddings.config.max_concurrent}
                        </span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Éxito:</span>
                        <span className={`stat-value ${getHealthColor(rateLimitStats.gemini_embeddings.statistics.success_rate)}`}>
                          {rateLimitStats.gemini_embeddings.statistics.success_rate.toFixed(1)}%
                        </span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Tiempo promedio:</span>
                        <span className="stat-value">
                          {formatTime(rateLimitStats.gemini_embeddings.statistics.average_response_time)}
                        </span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Rate limited:</span>
                        <span className="stat-value error">
                          {rateLimitStats.gemini_embeddings.statistics.rate_limited_calls}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="loading-state">Cargando estadísticas de rate limiting...</div>
            )}
          </div>

          {/* Estadísticas de Cola RAG */}
          <div className="stats-section">
            <h3>🔄 Cola de Procesamiento RAG</h3>
            {queueStats ? (
              <div className="queue-stats">
                <div className="queue-overview">
                  <div className="queue-card">
                    <h4>📋 Estado de la Cola</h4>
                    <div className="stat-grid">
                      <div className="stat-item">
                        <span className="stat-label">Pendientes:</span>
                        <span className="stat-value warning">{queueStats.queue_stats.pending_tasks}</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Procesando:</span>
                        <span className="stat-value processing">{queueStats.queue_stats.processing_tasks}</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Completadas:</span>
                        <span className="stat-value success">{queueStats.queue_stats.completed_tasks}</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Fallidas:</span>
                        <span className="stat-value error">{queueStats.queue_stats.failed_tasks}</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Éxito:</span>
                        <span className={`stat-value ${getHealthColor(queueStats.queue_stats.success_rate)}`}>
                          {queueStats.queue_stats.success_rate.toFixed(1)}%
                        </span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Tiempo promedio:</span>
                        <span className="stat-value">
                          {formatTime(queueStats.queue_stats.average_processing_time)}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="queue-card">
                    <h4>⚙️ Configuración</h4>
                    <div className="stat-grid">
                      <div className="stat-item">
                        <span className="stat-label">Workers máximos:</span>
                        <span className="stat-value">{queueStats.queue_info.max_concurrent_tasks}</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Workers activos:</span>
                        <span className="stat-value">{queueStats.queue_info.workers_active}</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Tamaño cola:</span>
                        <span className="stat-value">
                          {queueStats.queue_info.current_queue_size} / {queueStats.queue_info.max_queue_size}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Tareas Recientes */}
                {queueStats.recent_tasks && queueStats.recent_tasks.length > 0 && (
                  <div className="recent-tasks">
                    <h4>📝 Tareas Recientes</h4>
                    <div className="tasks-list">
                      {queueStats.recent_tasks.map((task) => (
                        <div key={task.id} className={`task-item ${task.status}`}>
                          <div className="task-info">
                            <span className="task-id">#{task.id.substring(0, 8)}</span>
                            <span className="task-book">Libro #{task.book_id}</span>
                            <span className={`task-status ${task.status}`}>
                              {task.status === 'pending' && '⏳ Pendiente'}
                              {task.status === 'processing' && '🔄 Procesando'}
                              {task.status === 'completed' && '✅ Completado'}
                              {task.status === 'failed' && '❌ Fallido'}
                            </span>
                            <span className="task-priority">{task.priority}</span>
                          </div>
                          {task.status === 'processing' && (
                            <div className="task-progress">
                              <div 
                                className="progress-fill" 
                                style={{ width: `${task.progress * 100}%` }}
                              ></div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="loading-state">Cargando estadísticas de cola...</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RateLimitMonitor;
