from .driver import DatabaseDriver
from .models import BaseModel
from .repository import BaseRepository
from .config import DatabaseConfig
from .query import QueryBuilder, Operator
from .relations import foreign_key, relationship, RelationType, MigrationManager
from .monitoring import HealthChecker
from .performance import AggregationManager
from .migrations import MigrationEngine, ModelRegistry

__version__ = "1.0.1"
__author__ = "Support Bot Team"

class Database:
    def __init__(self, db_path: str = None, enable_compression: bool = False):
        self.config = DatabaseConfig()
        if db_path is None:
            db_path = self.config.get_db_path()
        self.driver = DatabaseDriver(db_path, enable_compression)
        self.migration_engine = MigrationEngine(self.driver)
        self.health_checker = HealthChecker(self.driver)

    async def init_db(self):
        """Инициализация БД с автопоиском моделей"""
        ModelRegistry.discover_models()
        await self.migration_engine.init_migration_table()
        return ModelRegistry.get_models()

    async def upgrade(self):
        """Применение миграций"""
        ModelRegistry.discover_models()
        await self.migration_engine.upgrade()

    async def backup(self, backup_path: str = None):
        if backup_path is None:
            import os
            backup_dir = self.config.get_backup_dir()
            backup_path = os.path.join(backup_dir, f"backup_{int(__import__('time').time())}.json")
        await self.driver.backup(backup_path)
        return backup_path

    async def get_stats(self):
        return await self.driver.get_stats()
    
    async def get_metrics(self):
        return self.driver.get_metrics()
    
    async def health_check(self):
        return await self.health_checker.check_health()
    
    def add_middleware(self, middleware):
        self.driver.middleware_manager.add_middleware(middleware)
    
    def query(self, table_name: str) -> QueryBuilder:
        return self.driver.query(table_name)

__all__ = [
    'Database', 'DatabaseDriver', 'BaseModel', 'BaseRepository', 'DatabaseConfig',
    'QueryBuilder', 'Operator', 'foreign_key', 'relationship', 'RelationType',
    'MigrationEngine', 'ModelRegistry', 'HealthChecker', 'AggregationManager'
]