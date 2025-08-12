"""
Sistema robusto de Rate Limiting para llamadas a APIs de IA
Controla concurrencia, ventanas de tiempo y cola de procesamiento
"""

import asyncio
import threading
import time
from collections import defaultdict, deque
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class APIProvider(Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

@dataclass
class RateLimitConfig:
    """Configuración de límites de rate limiting"""
    max_concurrent_calls: int = 2  # Llamadas concurrentes máximas
    max_calls_per_minute: int = 30  # Llamadas por minuto
    max_calls_per_hour: int = 1000  # Llamadas por hora
    retry_delay: float = 1.0  # Delay base para retry
    max_retries: int = 3  # Máximo número de reintentos
    backoff_multiplier: float = 2.0  # Multiplicador para backoff exponencial
    queue_timeout: int = 300  # Timeout para elementos en cola (5 min)

class RateLimitStatus(Enum):
    SUCCESS = "success"
    RATE_LIMITED = "rate_limited"
    QUEUE_FULL = "queue_full"
    TIMEOUT = "timeout"
    ERROR = "error"

@dataclass
class CallStats:
    """Estadísticas de llamadas a API"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rate_limited_calls: int = 0
    average_response_time: float = 0.0
    last_call_time: float = 0.0

class RateLimiter:
    """
    Rate Limiter robusto con soporte para:
    - Límites de concurrencia
    - Límites por ventana de tiempo
    - Cola de procesamiento
    - Retry con backoff exponencial
    - Métricas y estadísticas
    """
    
    def __init__(self, provider: APIProvider, config: RateLimitConfig = None):
        self.provider = provider
        self.config = config or RateLimitConfig()
        
        # Control de concurrencia
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_calls)
        self.thread_semaphore = threading.Semaphore(self.config.max_concurrent_calls)
        
        # Ventanas de tiempo para rate limiting
        self.call_times_minute = deque()
        self.call_times_hour = deque()
        self.lock = threading.Lock()
        
        # Cola de procesamiento
        self.processing_queue = asyncio.Queue(maxsize=100)
        self.queue_workers_started = False
        
        # Estadísticas
        self.stats = CallStats()
        self.user_stats: Dict[str, CallStats] = defaultdict(CallStats)
        
        # Estado del sistema
        self.is_healthy = True
        self.last_error_time = 0
        self.error_count = 0

    def _cleanup_old_calls(self):
        """Limpia llamadas antiguas de las ventanas de tiempo"""
        current_time = time.time()
        
        # Limpiar ventana de minuto (60 segundos)
        while self.call_times_minute and current_time - self.call_times_minute[0] > 60:
            self.call_times_minute.popleft()
        
        # Limpiar ventana de hora (3600 segundos)
        while self.call_times_hour and current_time - self.call_times_hour[0] > 3600:
            self.call_times_hour.popleft()

    def _can_make_call(self) -> tuple[bool, str]:
        """Verifica si se puede realizar una llamada"""
        with self.lock:
            self._cleanup_old_calls()
            
            # Verificar límite por minuto
            if len(self.call_times_minute) >= self.config.max_calls_per_minute:
                wait_time = 60 - (time.time() - self.call_times_minute[0])
                return False, f"Límite por minuto alcanzado. Espera {wait_time:.1f}s"
            
            # Verificar límite por hora
            if len(self.call_times_hour) >= self.config.max_calls_per_hour:
                wait_time = 3600 - (time.time() - self.call_times_hour[0])
                return False, f"Límite por hora alcanzado. Espera {wait_time//60:.0f}m {wait_time%60:.0f}s"
            
            return True, "OK"

    def _record_call(self, success: bool = True, response_time: float = 0):
        """Registra una llamada en las estadísticas"""
        current_time = time.time()
        
        with self.lock:
            # Registrar en ventanas de tiempo
            self.call_times_minute.append(current_time)
            self.call_times_hour.append(current_time)
            
            # Actualizar estadísticas
            self.stats.total_calls += 1
            self.stats.last_call_time = current_time
            
            if success:
                self.stats.successful_calls += 1
            else:
                self.stats.failed_calls += 1
            
            # Actualizar tiempo de respuesta promedio
            if response_time > 0:
                total_time = self.stats.average_response_time * (self.stats.total_calls - 1)
                self.stats.average_response_time = (total_time + response_time) / self.stats.total_calls

    async def call_with_limit(self, 
                            func: Callable,
                            *args,
                            user_id: str = "anonymous",
                            timeout: float = 30.0,
                            **kwargs) -> Any:
        """
        Ejecuta una función con rate limiting y reintentos automáticos
        
        Args:
            func: Función a ejecutar
            *args: Argumentos posicionales
            user_id: ID del usuario (para estadísticas)
            timeout: Timeout para la llamada
            **kwargs: Argumentos nombrados
            
        Returns:
            Resultado de la función o excepción
        """
        
        last_exception = None
        retry_count = 0
        
        while retry_count <= self.config.max_retries:
            try:
                # Verificar si podemos hacer la llamada
                can_call, reason = self._can_make_call()
                if not can_call:
                    if retry_count < self.config.max_retries:
                        wait_time = self._extract_wait_time(reason)
                        logger.warning(f"Rate limit: {reason}. Reintentando en {wait_time:.1f}s (intento {retry_count + 1}/{self.config.max_retries + 1})")
                        await asyncio.sleep(wait_time)
                        retry_count += 1
                        continue
                    else:
                        logger.error(f"Rate limit: {reason}. Máximo de reintentos alcanzado.")
                        raise RateLimitExceeded(reason)
                
                # Adquirir semáforo para concurrencia
                async with self.semaphore:
                    start_time = time.time()
                    
                    try:
                        # Ejecutar la función
                        if asyncio.iscoroutinefunction(func):
                            result = await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
                        else:
                            # Para funciones síncronas, ejecutar en thread pool
                            loop = asyncio.get_event_loop()
                            result = await loop.run_in_executor(None, lambda: func(*args, **kwargs))
                        
                        response_time = time.time() - start_time
                        self._record_call(success=True, response_time=response_time)
                        
                        logger.info(f"API call successful ({self.provider.value}): {response_time:.2f}s")
                        return result
                        
                    except Exception as e:
                        response_time = time.time() - start_time
                        self._record_call(success=False, response_time=response_time)
                        
                        # Verificar si es un error de rate limiting
                        error_msg = str(e).lower()
                        if any(keyword in error_msg for keyword in ["quota", "rate", "limit", "429", "too many"]):
                            self.stats.rate_limited_calls += 1
                            logger.warning(f"Rate limit from API ({self.provider.value}): {e}")
                            
                            if retry_count < self.config.max_retries:
                                wait_time = self.config.retry_delay * (self.config.backoff_multiplier ** retry_count)
                                logger.info(f"Reintentando en {wait_time:.1f}s (intento {retry_count + 1}/{self.config.max_retries + 1})")
                                await asyncio.sleep(wait_time)
                                retry_count += 1
                                continue
                            else:
                                raise RateLimitExceeded(f"API rate limit: {e}")
                        
                        logger.error(f"API call failed ({self.provider.value}): {e}")
                        raise
                        
            except RateLimitExceeded as e:
                last_exception = e
                if retry_count < self.config.max_retries:
                    wait_time = self.config.retry_delay * (self.config.backoff_multiplier ** retry_count)
                    logger.info(f"Rate limit exceeded, reintentando en {wait_time:.1f}s (intento {retry_count + 1}/{self.config.max_retries + 1})")
                    await asyncio.sleep(wait_time)
                    retry_count += 1
                    continue
                else:
                    break
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error in call_with_limit: {e}")
                break
        
        # Si llegamos aquí, todos los reintentos fallaron
        if last_exception:
            raise last_exception
        else:
            raise Exception("Unknown error in call_with_limit")

    def _extract_wait_time(self, reason: str) -> float:
        """Extrae el tiempo de espera del mensaje de rate limit"""
        try:
            if "minuto" in reason:
                # Buscar el número de segundos en el mensaje
                import re
                match = re.search(r'(\d+\.?\d*)s', reason)
                if match:
                    return float(match.group(1))
            elif "hora" in reason:
                # Para límites por hora, usar un delay más corto
                return self.config.retry_delay
        except:
            pass
        
        # Fallback al delay configurado
        return self.config.retry_delay

    def call_with_limit_sync(self, 
                           func: Callable,
                           *args,
                           user_id: str = "anonymous",
                           **kwargs) -> Any:
        """
        Versión síncrona de call_with_limit con reintentos automáticos
        """
        
        last_exception = None
        retry_count = 0
        
        while retry_count <= self.config.max_retries:
            try:
                # Verificar si podemos hacer la llamada
                can_call, reason = self._can_make_call()
                if not can_call:
                    if retry_count < self.config.max_retries:
                        wait_time = self._extract_wait_time(reason)
                        logger.warning(f"Rate limit: {reason}. Reintentando en {wait_time:.1f}s (intento {retry_count + 1}/{self.config.max_retries + 1})")
                        time.sleep(wait_time)
                        retry_count += 1
                        continue
                    else:
                        logger.error(f"Rate limit: {reason}. Máximo de reintentos alcanzado.")
                        raise RateLimitExceeded(reason)
                
                # Adquirir semáforo para concurrencia
                with self.thread_semaphore:
                    start_time = time.time()
                    
                    try:
                        result = func(*args, **kwargs)
                        response_time = time.time() - start_time
                        self._record_call(success=True, response_time=response_time)
                        
                        logger.info(f"API call successful ({self.provider.value}): {response_time:.2f}s")
                        return result
                        
                    except Exception as e:
                        response_time = time.time() - start_time
                        self._record_call(success=False, response_time=response_time)
                        
                        # Verificar si es un error de rate limiting
                        error_msg = str(e).lower()
                        if any(keyword in error_msg for keyword in ["quota", "rate", "limit", "429", "too many"]):
                            self.stats.rate_limited_calls += 1
                            logger.warning(f"Rate limit from API ({self.provider.value}): {e}")
                            
                            if retry_count < self.config.max_retries:
                                wait_time = self.config.retry_delay * (self.config.backoff_multiplier ** retry_count)
                                logger.info(f"Reintentando en {wait_time:.1f}s (intento {retry_count + 1}/{self.config.max_retries + 1})")
                                time.sleep(wait_time)
                                retry_count += 1
                                continue
                            else:
                                raise RateLimitExceeded(f"API rate limit: {e}")
                        
                        logger.error(f"API call failed ({self.provider.value}): {e}")
                        raise
                        
            except RateLimitExceeded as e:
                last_exception = e
                if retry_count < self.config.max_retries:
                    wait_time = self.config.retry_delay * (self.config.backoff_multiplier ** retry_count)
                    logger.info(f"Rate limit exceeded, reintentando en {wait_time:.1f}s (intento {retry_count + 1}/{self.config.max_retries + 1})")
                    time.sleep(wait_time)
                    retry_count += 1
                    continue
                else:
                    break
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error in call_with_limit_sync: {e}")
                break
        
        # Si llegamos aquí, todos los reintentos fallaron
        if last_exception:
            raise last_exception
        else:
            raise Exception("Unknown error in call_with_limit_sync")

    def get_stats(self) -> dict:
        """Obtiene estadísticas del rate limiter"""
        with self.lock:
            current_time = time.time()
            self._cleanup_old_calls()
            
            return {
                "provider": self.provider.value,
                "config": {
                    "max_concurrent": self.config.max_concurrent_calls,
                    "max_per_minute": self.config.max_calls_per_minute,
                    "max_per_hour": self.config.max_calls_per_hour
                },
                "current_usage": {
                    "calls_this_minute": len(self.call_times_minute),
                    "calls_this_hour": len(self.call_times_hour),
                    "concurrent_calls": self.config.max_concurrent_calls - self.semaphore._value
                },
                "statistics": {
                    "total_calls": self.stats.total_calls,
                    "successful_calls": self.stats.successful_calls,
                    "failed_calls": self.stats.failed_calls,
                    "rate_limited_calls": self.stats.rate_limited_calls,
                    "success_rate": self.stats.successful_calls / max(1, self.stats.total_calls) * 100,
                    "average_response_time": self.stats.average_response_time,
                    "last_call_time": self.stats.last_call_time
                },
                "health": {
                    "is_healthy": self.is_healthy,
                    "error_count": self.error_count
                }
            }

    def reset_stats(self):
        """Reinicia las estadísticas"""
        with self.lock:
            self.stats = CallStats()
            self.user_stats.clear()
            self.call_times_minute.clear()
            self.call_times_hour.clear()


class RateLimitExceeded(Exception):
    """Excepción lanzada cuando se excede el rate limit"""
    pass


# ============================================================================
# INSTANCIAS GLOBALES DE RATE LIMITERS
# ============================================================================

# Configuraciones específicas por proveedor
GEMINI_CONFIG = RateLimitConfig(
    max_concurrent_calls=10,  # Aumentado de 5 a 10 para mejor rendimiento
    max_calls_per_minute=60,  # Aumentado de 15 a 60 (1 por segundo)
    max_calls_per_hour=2000,  # Aumentado de 300 a 2000
    retry_delay=0.5,  # Reducido de 1.0 a 0.5 segundos
    max_retries=5,  # Aumentado de 3 a 5 reintentos
    backoff_multiplier=1.3  # Reducido de 1.5 a 1.3 para reintentos más rápidos
)

GEMINI_EMBEDDINGS_CONFIG = RateLimitConfig(
    max_concurrent_calls=15,  # Aumentado de 5 a 15 para embeddings
    max_calls_per_minute=120,  # Aumentado de 30 a 120 (2 por segundo)
    max_calls_per_hour=5000,  # Aumentado de 1000 a 5000
    retry_delay=0.2,  # Reducido de 0.5 a 0.2 segundos
    max_retries=8,  # Aumentado de 5 a 8 reintentos
    backoff_multiplier=1.1  # Reducido de 1.2 a 1.1 para reintentos más rápidos
)

# Rate limiters globales
gemini_limiter = RateLimiter(APIProvider.GEMINI, GEMINI_CONFIG)
gemini_embeddings_limiter = RateLimiter(APIProvider.GEMINI, GEMINI_EMBEDDINGS_CONFIG)


# ============================================================================
# FUNCIONES DE CONVENIENCIA
# ============================================================================

async def call_gemini_with_limit(func: Callable, *args, **kwargs):
    """Wrapper para llamadas a Gemini con rate limiting"""
    return await gemini_limiter.call_with_limit(func, *args, **kwargs)

def call_gemini_with_limit_sync(func: Callable, *args, **kwargs):
    """Wrapper síncrono para llamadas a Gemini con rate limiting"""
    return gemini_limiter.call_with_limit_sync(func, *args, **kwargs)

async def call_gemini_embeddings_with_limit(func: Callable, *args, **kwargs):
    """Wrapper para llamadas a embeddings de Gemini con rate limiting"""
    return await gemini_embeddings_limiter.call_with_limit(func, *args, **kwargs)

def call_gemini_embeddings_with_limit_sync(func: Callable, *args, **kwargs):
    """Wrapper síncrono para llamadas a embeddings de Gemini con rate limiting"""
    return gemini_embeddings_limiter.call_with_limit_sync(func, *args, **kwargs)

def get_all_rate_limit_stats() -> dict:
    """Obtiene estadísticas de todos los rate limiters"""
    return {
        "gemini_analysis": gemini_limiter.get_stats(),
        "gemini_embeddings": gemini_embeddings_limiter.get_stats()
    }
