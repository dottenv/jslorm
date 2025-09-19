import os
import importlib
import inspect
from typing import Dict, List, Type
from .models import BaseModel
from .driver import DatabaseDriver

class ModelRegistry:
    _models: Dict[str, Type[BaseModel]] = {}
    _app_path: str = None

    @classmethod
    def register_model(cls, model_class: Type[BaseModel]):
        table_name = model_class.get_table_name()
        cls._models[table_name] = model_class

    @classmethod
    def get_models(cls) -> Dict[str, Type[BaseModel]]:
        return cls._models

    @classmethod
    def discover_models(cls, app_path: str = None):
        """Автоматически находит все модели в проекте"""
        if app_path:
            cls._app_path = app_path
        
        if not cls._app_path:
            cls._app_path = os.getcwd()
        
        # Сканируем все .py файлы в проекте
        for root, dirs, files in os.walk(cls._app_path):
            # Пропускаем системные папки
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'env']]
            
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    file_path = os.path.join(root, file)
                    cls._scan_file_for_models(file_path)

    @classmethod
    def _scan_file_for_models(cls, file_path: str):
        """Сканирует файл на наличие моделей"""
        try:
            import sys
            import importlib.util
            
            # Получаем имя модуля
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # Импортируем модуль
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                # Ищем классы-наследники BaseModel
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (obj.__module__ == module_name and 
                        issubclass(obj, BaseModel) and 
                        obj != BaseModel and 
                        hasattr(obj, '__table_name__') and 
                        obj.__table_name__):
                        cls.register_model(obj)
                        print(f"✅ Found model: {obj.__name__} -> {obj.__table_name__}")
                        
        except Exception as e:
            # Игнорируем ошибки импорта
            print(f"⚠️  Error scanning {file_path}: {e}")
            pass

class MigrationEngine:
    def __init__(self, db_driver: DatabaseDriver):
        self.db = db_driver
        self.migration_table = "_jslorm_migrations"

    async def init_migration_table(self):
        """Создает таблицу для отслеживания миграций"""
        await self.db.create_table(self.migration_table, {
            "id": "int",
            "version": "str", 
            "applied_at": "str",
            "models_hash": "str"
        })

    async def get_current_version(self) -> str:
        """Получает текущую версию миграций"""
        try:
            record = await self.db.select_one(self.migration_table, {})
            return record.get("version", "0") if record else "0"
        except:
            return "0"

    async def get_models_hash(self) -> str:
        """Генерирует хэш всех моделей для отслеживания изменений"""
        import hashlib
        models = ModelRegistry.get_models()
        models_data = {}
        
        for table_name, model_class in models.items():
            models_data[table_name] = {
                "schema": model_class.get_schema(),
                "indexes": model_class.get_indexes(),
                "unique_fields": model_class.get_unique_fields()
            }
        
        models_str = str(sorted(models_data.items()))
        return hashlib.md5(models_str.encode()).hexdigest()

    async def detect_changes(self) -> Dict[str, any]:
        """Определяет изменения в моделях"""
        current_hash = await self.get_models_hash()
        
        try:
            last_migration = await self.db.select_one(self.migration_table, {})
            last_hash = last_migration.get("models_hash", "") if last_migration else ""
        except:
            last_hash = ""
        
        if current_hash != last_hash:
            return {
                "has_changes": True,
                "current_hash": current_hash,
                "last_hash": last_hash,
                "models": ModelRegistry.get_models()
            }
        
        return {"has_changes": False}

    async def create_migration(self, version: str = None):
        """Создает новую миграцию"""
        if not version:
            from datetime import datetime
            version = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        changes = await self.detect_changes()
        if not changes["has_changes"]:
            print("No changes detected")
            return
        
        # Создаем все таблицы из моделей
        models = ModelRegistry.get_models()
        for table_name, model_class in models.items():
            schema = model_class.get_schema()
            await self.db.create_table(table_name, schema)
            
            # Создаем индексы
            for field in model_class.get_indexes():
                self.db.index_manager.create_index(table_name, field)
        
        # Записываем миграцию
        await self.init_migration_table()
        
        # Удаляем старые записи миграций
        await self.db.delete(self.migration_table, {})
        
        # Добавляем новую запись
        await self.db.insert(self.migration_table, {
            "version": version,
            "applied_at": datetime.now().isoformat(),
            "models_hash": changes["current_hash"]
        })
        
        print(f"✅ Migration {version} applied successfully")
        print(f"📊 Created {len(models)} tables")

    async def upgrade(self):
        """Применяет миграции (создает/обновляет таблицы)"""
        await self.create_migration()

    async def show_status(self):
        """Показывает статус миграций"""
        changes = await self.detect_changes()
        current_version = await self.get_current_version()
        models = ModelRegistry.get_models()
        
        print(f"📋 Migration Status:")
        print(f"Current version: {current_version}")
        print(f"Models found: {len(models)}")
        print(f"Changes detected: {'Yes' if changes['has_changes'] else 'No'}")
        
        if models:
            print(f"\n📊 Registered Models:")
            for table_name, model_class in models.items():
                schema = model_class.get_schema()
                print(f"  • {table_name}: {len(schema)} fields")

# Автоматическая регистрация моделей при импорте
def auto_register_model(cls):
    """Декоратор для автоматической регистрации модели"""
    ModelRegistry.register_model(cls)
    return cls