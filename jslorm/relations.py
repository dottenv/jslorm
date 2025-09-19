from typing import Dict, Any, List, Optional, Type, Union, ForwardRef
from pydantic import BaseModel as PydanticBaseModel, Field
from enum import Enum

class RelationType(str, Enum):
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"

class ForeignKey:
    def __init__(self, to_table: str, on_delete: str = "CASCADE"):
        self.to_table = to_table
        self.on_delete = on_delete

class Relationship:
    def __init__(self, 
                 to_model: Union[str, Type], 
                 relation_type: RelationType,
                 foreign_key: Optional[str] = None,
                 back_populates: Optional[str] = None):
        self.to_model = to_model
        self.relation_type = relation_type
        self.foreign_key = foreign_key
        self.back_populates = back_populates

def foreign_key(to_table: str, on_delete: str = "CASCADE"):
    return Field(default=None, description=f"FK:{to_table}:{on_delete}")

def relationship(to_model: Union[str, Type], 
                relation_type: RelationType = RelationType.ONE_TO_MANY,
                foreign_key: Optional[str] = None,
                back_populates: Optional[str] = None):
    return Field(default=None, 
                description=f"REL:{to_model}:{relation_type}:{foreign_key}:{back_populates}")

class ValidationRule:
    def __init__(self, field: str, rule: str, message: str):
        self.field = field
        self.rule = rule
        self.message = message

class SchemaValidator:
    @staticmethod
    def validate_foreign_keys(record: Dict[str, Any], schema: Dict[str, str], 
                            all_tables: Dict[str, Any]) -> List[str]:
        errors = []
        for field_name, field_info in schema.items():
            if field_info.startswith("FK:"):
                parts = field_info.split(":")
                target_table = parts[1]
                fk_value = record.get(field_name)
                
                if fk_value is not None:
                    # Проверяем существование записи в целевой таблице
                    target_records = all_tables.get(target_table, {}).get("records", [])
                    if not any(r.get("id") == fk_value for r in target_records):
                        errors.append(f"Foreign key {field_name} references non-existent record")
        return errors

    @staticmethod
    def validate_unique_constraints(record: Dict[str, Any], 
                                  existing_records: List[Dict[str, Any]],
                                  unique_fields: List[str]) -> List[str]:
        errors = []
        record_id = record.get("id")
        
        for field in unique_fields:
            value = record.get(field)
            if value is not None:
                for existing in existing_records:
                    if (existing.get("id") != record_id and 
                        existing.get(field) == value):
                        errors.append(f"Field {field} must be unique")
                        break
        return errors

class MigrationManager:
    def __init__(self):
        self.migrations = []

    def add_migration(self, version: str, up_func, down_func):
        self.migrations.append({
            "version": version,
            "up": up_func,
            "down": down_func
        })

    async def apply_migrations(self, db_driver, target_version: Optional[str] = None):
        current_version = await self._get_current_version(db_driver)
        
        for migration in self.migrations:
            if target_version and migration["version"] > target_version:
                break
            if migration["version"] > current_version:
                await migration["up"](db_driver)
                await self._set_version(db_driver, migration["version"])

    async def rollback_migration(self, db_driver, target_version: str):
        current_version = await self._get_current_version(db_driver)
        
        for migration in reversed(self.migrations):
            if migration["version"] <= target_version:
                break
            if migration["version"] <= current_version:
                await migration["down"](db_driver)
                await self._set_version(db_driver, migration["version"])

    async def _get_current_version(self, db_driver) -> str:
        try:
            version_record = await db_driver.select_one("_migrations", {})
            return version_record.get("version", "0.0.0") if version_record else "0.0.0"
        except:
            return "0.0.0"

    async def _set_version(self, db_driver, version: str):
        await db_driver.create_table("_migrations", {"version": "str"})
        existing = await db_driver.select_one("_migrations", {})
        if existing:
            await db_driver.update("_migrations", {"id": existing["id"]}, {"version": version})
        else:
            await db_driver.insert("_migrations", {"version": version})