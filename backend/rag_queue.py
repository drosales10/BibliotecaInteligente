"""
Sistema de cola inteligente para procesamiento RAG
Gestiona la cola de procesamiento, prioridades y feedback en tiempo real
"""

import asyncio
import threading
import time
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from queue import PriorityQueue, Empty
import logging
import uuid

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = 3
    NORMAL = 2
    HIGH = 1
    URGENT = 0

@dataclass
class RAGTask:
    """Tarea de procesamiento RAG"""
    id: str
    book_id: int
    file_path: str
    rag_book_id: str
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0  # 0.0 - 1.0
    error_message: Optional[str] = None
    user_id: str = "anonymous"
    
    def __lt__(self, other):
        """Para sorting en PriorityQueue"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.created_at < other.created_at

@dataclass
class QueueStats:
    """Estadísticas de la cola"""
    total_tasks: int = 0
    pending_tasks: int = 0
    processing_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_processing_time: float = 0.0
    queue_wait_time: float = 0.0

class RAGQueue:
    """
    Cola inteligente para procesamiento RAG con:
    - Prioridades
    - Límites de concurrencia
    - Progreso en tiempo real
    - Estadísticas
    - Cancelación de tareas
    """
    
    def __init__(self, max_concurrent_tasks: int = 2, max_queue_size: int = 100):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.max_queue_size = max_queue_size
        
        # Cola principal con prioridades
        self.task_queue = PriorityQueue(maxsize=max_queue_size)
        
        # Control de tareas
        self.tasks: Dict[str, RAGTask] = {}
        self.processing_tasks: Dict[str, RAGTask] = {}
        self.completed_tasks: Dict[str, RAGTask] = {}
        
        # Control de concurrencia
        self.semaphore = threading.Semaphore(max_concurrent_tasks)
        self.lock = threading.Lock()
        
        # Workers
        self.workers_started = False
        self.stop_workers = False
        self.worker_threads: List[threading.Thread] = []
        
        # Estadísticas
        self.stats = QueueStats()
        
        # Callbacks para notificaciones
        self.progress_callbacks: List[Callable] = []
        self.completion_callbacks: List[Callable] = []

    def add_task(self, 
                book_id: int, 
                file_path: str, 
                rag_book_id: str,
                priority: TaskPriority = TaskPriority.NORMAL,
                user_id: str = "anonymous") -> str:
        """
        Agrega una nueva tarea a la cola
        
        Returns:
            task_id: ID único de la tarea
        """
        with self.lock:
            # Verificar si la cola está llena
            if self.task_queue.full():
                raise Exception("Cola de procesamiento llena. Intenta más tarde.")
            
            # Crear tarea
            task_id = str(uuid.uuid4())
            task = RAGTask(
                id=task_id,
                book_id=book_id,
                file_path=file_path,
                rag_book_id=rag_book_id,
                priority=priority,
                user_id=user_id
            )
            
            # Agregar a la cola y tracking
            self.task_queue.put(task)
            self.tasks[task_id] = task
            self.stats.total_tasks += 1
            self.stats.pending_tasks += 1
            
            logger.info(f"Tarea RAG agregada: {task_id} (prioridad: {priority.name})")
            
            # Iniciar workers si no están corriendo
            if not self.workers_started:
                self.start_workers()
            
            return task_id

    def get_task_status(self, task_id: str) -> Optional[RAGTask]:
        """Obtiene el estado de una tarea"""
        with self.lock:
            return self.tasks.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """Cancela una tarea pendiente"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return False
            
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                self.stats.pending_tasks -= 1
                logger.info(f"Tarea cancelada: {task_id}")
                return True
            
            return False

    def get_queue_position(self, task_id: str) -> int:
        """Obtiene la posición de una tarea en la cola"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task or task.status != TaskStatus.PENDING:
                return -1
            
            # Contar tareas con mayor prioridad
            position = 1
            for other_task in self.tasks.values():
                if (other_task.status == TaskStatus.PENDING and 
                    other_task.id != task_id and
                    other_task < task):
                    position += 1
            
            return position

    def start_workers(self):
        """Inicia los workers de procesamiento"""
        if self.workers_started:
            return
        
        self.workers_started = True
        self.stop_workers = False
        
        # Crear workers
        for i in range(self.max_concurrent_tasks):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"RAGWorker-{i}",
                daemon=True
            )
            worker.start()
            self.worker_threads.append(worker)
        
        logger.info(f"Iniciados {self.max_concurrent_tasks} workers RAG")

    def stop_workers(self):
        """Detiene los workers"""
        self.stop_workers = True
        self.workers_started = False
        
        # Esperar a que terminen los workers
        for worker in self.worker_threads:
            worker.join(timeout=5.0)
        
        self.worker_threads.clear()
        logger.info("Workers RAG detenidos")

    def _worker_loop(self):
        """Loop principal del worker"""
        while not self.stop_workers:
            try:
                # Intentar obtener una tarea (con timeout)
                try:
                    task = self.task_queue.get(timeout=1.0)
                except Empty:
                    continue
                
                # Adquirir semáforo
                self.semaphore.acquire()
                
                try:
                    # Procesar la tarea
                    self._process_task(task)
                finally:
                    self.semaphore.release()
                    self.task_queue.task_done()
                    
            except Exception as e:
                logger.error(f"Error en worker RAG: {e}")

    def _process_task(self, task: RAGTask):
        """Procesa una tarea individual"""
        try:
            with self.lock:
                task.status = TaskStatus.PROCESSING
                task.started_at = datetime.now()
                self.processing_tasks[task.id] = task
                self.stats.pending_tasks -= 1
                self.stats.processing_tasks += 1
            
            logger.info(f"Iniciando procesamiento RAG: {task.id}")
            
            # Notificar inicio
            self._notify_progress(task)
            
            # Procesar con RAG
            result = self._execute_rag_processing(task)
            
            with self.lock:
                if result["success"]:
                    task.status = TaskStatus.COMPLETED
                    task.progress = 1.0
                    task.completed_at = datetime.now()
                    self.completed_tasks[task.id] = task
                    self.stats.completed_tasks += 1
                else:
                    task.status = TaskStatus.FAILED
                    task.error_message = result["error"]
                    self.stats.failed_tasks += 1
                
                # Remover de processing
                if task.id in self.processing_tasks:
                    del self.processing_tasks[task.id]
                self.stats.processing_tasks -= 1
                
                # Actualizar tiempo promedio
                if task.started_at and task.completed_at:
                    processing_time = (task.completed_at - task.started_at).total_seconds()
                    self._update_average_processing_time(processing_time)
            
            # Notificar finalización
            self._notify_completion(task)
            
            logger.info(f"Procesamiento RAG completado: {task.id} - {task.status.value}")
            
        except Exception as e:
            with self.lock:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                if task.id in self.processing_tasks:
                    del self.processing_tasks[task.id]
                self.stats.processing_tasks -= 1
                self.stats.failed_tasks += 1
            
            logger.error(f"Error procesando tarea RAG {task.id}: {e}")

    def _execute_rag_processing(self, task: RAGTask) -> dict:
        """Ejecuta el procesamiento RAG real"""
        try:
            import rag
            
            # Actualizar progreso: iniciando
            task.progress = 0.1
            self._notify_progress(task)
            
            # Procesar libro para RAG
            result = asyncio.run(rag.process_book_for_rag(task.file_path, task.rag_book_id))
            
            # Actualizar progreso: completado
            task.progress = 0.9
            self._notify_progress(task)
            
            return {"success": True, "result": result}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _update_average_processing_time(self, processing_time: float):
        """Actualiza el tiempo promedio de procesamiento"""
        if self.stats.completed_tasks == 1:
            self.stats.average_processing_time = processing_time
        else:
            # Media móvil
            alpha = 0.1  # Factor de suavizado
            self.stats.average_processing_time = (
                alpha * processing_time + 
                (1 - alpha) * self.stats.average_processing_time
            )

    def _notify_progress(self, task: RAGTask):
        """Notifica progreso a los callbacks"""
        for callback in self.progress_callbacks:
            try:
                callback(task)
            except Exception as e:
                logger.error(f"Error en callback de progreso: {e}")

    def _notify_completion(self, task: RAGTask):
        """Notifica finalización a los callbacks"""
        for callback in self.completion_callbacks:
            try:
                callback(task)
            except Exception as e:
                logger.error(f"Error en callback de finalización: {e}")

    def add_progress_callback(self, callback: Callable):
        """Agrega un callback para notificaciones de progreso"""
        self.progress_callbacks.append(callback)

    def add_completion_callback(self, callback: Callable):
        """Agrega un callback para notificaciones de finalización"""
        self.completion_callbacks.append(callback)

    def get_stats(self) -> dict:
        """Obtiene estadísticas de la cola"""
        with self.lock:
            return {
                "queue_stats": {
                    "total_tasks": self.stats.total_tasks,
                    "pending_tasks": self.stats.pending_tasks,
                    "processing_tasks": self.stats.processing_tasks,
                    "completed_tasks": self.stats.completed_tasks,
                    "failed_tasks": self.stats.failed_tasks,
                    "success_rate": (
                        self.stats.completed_tasks / max(1, self.stats.total_tasks) * 100
                    ),
                    "average_processing_time": self.stats.average_processing_time
                },
                "queue_info": {
                    "max_concurrent_tasks": self.max_concurrent_tasks,
                    "max_queue_size": self.max_queue_size,
                    "current_queue_size": self.task_queue.qsize(),
                    "workers_active": len(self.processing_tasks)
                },
                "recent_tasks": [
                    {
                        "id": task.id,
                        "book_id": task.book_id,
                        "status": task.status.value,
                        "progress": task.progress,
                        "created_at": task.created_at.isoformat(),
                        "priority": task.priority.name
                    }
                    for task in list(self.tasks.values())[-10:]  # Últimas 10 tareas
                ]
            }

    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Limpia tareas antiguas completadas/fallidas"""
        with self.lock:
            current_time = datetime.now()
            to_remove = []
            
            for task_id, task in self.tasks.items():
                if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                    task.completed_at and
                    (current_time - task.completed_at).total_seconds() > max_age_hours * 3600):
                    to_remove.append(task_id)
            
            for task_id in to_remove:
                del self.tasks[task_id]
                if task_id in self.completed_tasks:
                    del self.completed_tasks[task_id]
            
            logger.info(f"Limpiadas {len(to_remove)} tareas antiguas")


# ============================================================================
# INSTANCIA GLOBAL DE LA COLA RAG
# ============================================================================

# Cola global para procesamiento RAG
rag_queue = RAGQueue(max_concurrent_tasks=2, max_queue_size=50)

def get_rag_queue() -> RAGQueue:
    """Obtiene la instancia global de la cola RAG"""
    return rag_queue
