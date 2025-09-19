from typing import List, Optional, Dict, Any, Type, Union
from .driver import DatabaseDriver
from .models import BaseModel
from .query import QueryBuilder, Operator
from .monitoring import DatabaseLogger, MetricsCollector

class BaseRepository:
    def __init__(self, db_driver: DatabaseDriver, model_class: Type[BaseModel]):
        self.db = db_driver
        self.model_class = model_class
        self.table = model_class.get_table_name()

    async def create_table(self):
        schema = self.model_class.get_schema()
        await self.db.create_table(self.table, schema)
        
        # Создаем индексы
        for field in self.model_class.get_indexes():
            self.db.index_manager.create_index(self.table, field)

    async def create(self, model: BaseModel) -> BaseModel:
        data = model.dict(exclude={'id', 'created_at', 'updated_at'})
        record_id = await self.db.insert(self.table, data)
        return await self.get_by_id(record_id)

    async def get_by_id(self, id: int) -> Optional[BaseModel]:
        data = await self.db.select_one(self.table, {"id": id})
        return self.model_class(**data) if data else None

    async def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[BaseModel]:
        query = self.db.query(self.table)
        if limit:
            query.limit(limit)
        if offset:
            query.offset(offset)
        
        records = await self.db.select(self.table, query_builder=query)
        return [self.model_class(**record) for record in records]

    async def find(self, where: Dict[str, Any] = None, **kwargs) -> List[BaseModel]:
        query = self.db.query(self.table)
        
        # Поддержка операторов в kwargs
        for field, value in kwargs.items():
            if '__' in field:
                field_name, operator = field.split('__', 1)
                query.where(field_name, operator, value)
            else:
                query.where(field, Operator.EQ, value)
        
        # Обычные where условия
        if where:
            for field, value in where.items():
                query.where(field, Operator.EQ, value)
        
        records = await self.db.select(self.table, query_builder=query)
        return [self.model_class(**record) for record in records]

    async def find_one(self, where: Dict[str, Any] = None, **kwargs) -> Optional[BaseModel]:
        results = await self.find(where, **kwargs)
        return results[0] if results else None

    async def where(self, field: str, operator: Union[str, Operator], value: Any):
        query = self.db.query(self.table).where(field, operator, value)
        records = await self.db.select(self.table, query_builder=query)
        return [self.model_class(**record) for record in records]

    async def order_by(self, field: str, desc: bool = False):
        query = self.db.query(self.table).order_by(field, desc)
        records = await self.db.select(self.table, query_builder=query)
        return [self.model_class(**record) for record in records]

    async def count(self, where: Dict[str, Any] = None) -> int:
        return await self.db.aggregate(self.table, "count", "id", where)

    async def sum(self, field: str, where: Dict[str, Any] = None) -> Union[int, float]:
        return await self.db.aggregate(self.table, "sum", field, where)

    async def avg(self, field: str, where: Dict[str, Any] = None) -> float:
        return await self.db.aggregate(self.table, "avg", field, where)

    async def update(self, id: int, updates: Dict[str, Any]) -> bool:
        return await self.db.update(self.table, {"id": id}, updates) > 0

    async def delete(self, id: int) -> bool:
        return await self.db.delete(self.table, {"id": id}) > 0