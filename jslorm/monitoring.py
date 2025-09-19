import logging
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from functools import wraps
import asyncio

class DatabaseLogger:
    def __init__(self, name: str = "jslorm"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log_query(self, operation: str, table: str, duration: float, 
                  query: Optional[Dict[str, Any]] = None):
        self.logger.info(f"{operation} on {table} took {duration:.3f}s - Query: {query}")

    def log_error(self, operation: str, table: str, error: Exception):
        self.logger.error(f"Error in {operation} on {table}: {str(error)}")

class MetricsCollector:
    def __init__(self):
        self.metrics = {
            "queries": 0,
            "inserts": 0,
            "updates": 0,
            "deletes": 0,
            "selects": 0,
            "total_time": 0.0,
            "avg_query_time": 0.0,
            "errors": 0
        }
        self.query_times = []

    def record_query(self, operation: str, duration: float):
        self.metrics["queries"] += 1
        self.metrics[f"{operation}s"] = self.metrics.get(f"{operation}s", 0) + 1
        self.metrics["total_time"] += duration
        self.query_times.append(duration)
        
        # Обновляем среднее время
        self.metrics["avg_query_time"] = self.metrics["total_time"] / self.metrics["queries"]

    def record_error(self):
        self.metrics["errors"] += 1

    def get_metrics(self) -> Dict[str, Any]:
        return {
            **self.metrics,
            "min_query_time": min(self.query_times) if self.query_times else 0,
            "max_query_time": max(self.query_times) if self.query_times else 0
        }

    def reset_metrics(self):
        self.metrics = {k: 0 if isinstance(v, (int, float)) else v for k, v in self.metrics.items()}
        self.query_times = []

class MiddlewareManager:
    def __init__(self):
        self.middlewares = []

    def add_middleware(self, middleware: Callable):
        self.middlewares.append(middleware)

    async def execute_middlewares(self, operation: str, table: str, data: Any, 
                                context: Dict[str, Any]) -> Any:
        result = data
        for middleware in self.middlewares:
            if asyncio.iscoroutinefunction(middleware):
                result = await middleware(operation, table, result, context)
            else:
                result = middleware(operation, table, result, context)
        return result

def timed_operation(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        start_time = time.time()
        operation = func.__name__
        table = getattr(self, 'table', 'unknown')
        
        try:
            result = await func(self, *args, **kwargs)
            duration = time.time() - start_time
            
            # Используем logger и metrics из self, если есть
            if hasattr(self, 'logger'):
                self.logger.log_query(operation, table, duration, kwargs.get('where'))
            if hasattr(self, 'metrics'):
                self.metrics.record_query(operation, duration)
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            if hasattr(self, 'logger'):
                self.logger.log_error(operation, table, e)
            if hasattr(self, 'metrics'):
                self.metrics.record_error()
            raise
    return wrapper

def cached(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        # Кэшируем только SELECT операции
        if func.__name__ in ['select', 'select_one', 'find', 'get_all', 'get_by_id']:
            # Простое кэширование - можно расширить позже
            if hasattr(self, '_cache'):
                table = getattr(self, 'table', 'unknown')
                cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
                
                if cache_key in self._cache:
                    return self._cache[cache_key]
                
                result = await func(self, *args, **kwargs)
                self._cache[cache_key] = result
                return result
        
        return await func(self, *args, **kwargs)
    return wrapper

def validate_input(validator_func: Callable):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Валидируем входные данные
            validation_errors = validator_func(*args, **kwargs)
            if validation_errors:
                raise ValueError(f"Validation errors: {validation_errors}")
            
            return await func(self, *args, **kwargs)
        return wrapper
    return decorator

class HealthChecker:
    def __init__(self, db_driver):
        self.db_driver = db_driver

    async def check_health(self) -> Dict[str, Any]:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }

        try:
            # Проверяем доступность файлов БД
            import os
            data_file_exists = os.path.exists(self.db_driver.data_path)
            index_file_exists = os.path.exists(self.db_driver.index_path)
            
            health_status["checks"]["data_file"] = {
                "status": "ok" if data_file_exists else "error",
                "path": self.db_driver.data_path
            }
            
            health_status["checks"]["index_file"] = {
                "status": "ok" if index_file_exists else "error", 
                "path": self.db_driver.index_path
            }

            # Проверяем возможность чтения данных
            try:
                stats = await self.db_driver.get_stats()
                health_status["checks"]["read_access"] = {
                    "status": "ok",
                    "tables_count": len(stats.get("tables", {}))
                }
            except Exception as e:
                health_status["checks"]["read_access"] = {
                    "status": "error",
                    "error": str(e)
                }
                health_status["status"] = "unhealthy"

        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)

        return health_status