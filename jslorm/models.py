from pydantic import BaseModel as PydanticBaseModel, Field
from typing import Optional, Dict, Any, ClassVar, List
from .relations import foreign_key, relationship, RelationType

class BaseModelMeta(type(PydanticBaseModel)):
    """Метакласс для автоматической регистрации моделей"""
    def __new__(cls, name, bases, namespace, **kwargs):
        new_class = super().__new__(cls, name, bases, namespace, **kwargs)
        
        # Регистрируем модель если это не базовый класс
        if name != 'BaseModel' and hasattr(new_class, '__table_name__'):
            # Отложенная регистрация через импорт
            try:
                from .migrations import ModelRegistry
                ModelRegistry.register_model(new_class)
            except ImportError:
                # Модуль миграций еще не загружен
                pass
        
        return new_class

class BaseModel(PydanticBaseModel, metaclass=BaseModelMeta):
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # Метаданные для таблицы
    __table_name__: ClassVar[str] = ""
    __schema__: ClassVar[Dict[str, str]] = {}
    __indexes__: ClassVar[List[str]] = []
    __unique_fields__: ClassVar[List[str]] = []
    
    class Config:
        from_attributes = True
    
    @classmethod
    def get_table_name(cls) -> str:
        return cls.__table_name__ or cls.__name__.lower()
    
    @classmethod
    def get_schema(cls) -> Dict[str, str]:
        if cls.__schema__:
            return cls.__schema__
        
        # Автогенерация схемы из полей модели
        schema = {}
        for field_name, field_info in cls.__fields__.items():
            field_type = field_info.type_
            if field_type == int:
                schema[field_name] = "int"
            elif field_type == str:
                schema[field_name] = "str"
            elif field_type == bool:
                schema[field_name] = "bool"
            else:
                schema[field_name] = "str"
        return schema
    
    @classmethod
    def get_indexes(cls) -> List[str]:
        return cls.__indexes__
    
    @classmethod
    def get_unique_fields(cls) -> List[str]:
        return cls.__unique_fields__