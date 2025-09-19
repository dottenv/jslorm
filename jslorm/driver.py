import json
import os
import asyncio
import aiofiles
from typing import Dict, List, Any, Optional
from datetime import datetime
from .performance import IndexManager, CacheManager, CompressionManager, AggregationManager
from .monitoring import DatabaseLogger, MetricsCollector, MiddlewareManager, timed_operation
from .query import QueryBuilder

class DatabaseDriver:
    def __init__(self, db_path: str, enable_compression: bool = False):
        self.db_path = db_path
        self.data_path = f"{db_path}.data"
        self.index_path = f"{db_path}.idx"
        self.lock = asyncio.Lock()
        self.enable_compression = enable_compression
        
        # Инициализируем компоненты производительности
        self.index_manager = IndexManager()
        self.cache_manager = CacheManager()
        self.logger = DatabaseLogger()
        self.metrics = MetricsCollector()
        self.middleware_manager = MiddlewareManager()
        
        self._init_db()

    def _init_db(self):
        if not os.path.exists(self.data_path):
            with open(self.data_path, 'w') as f:
                json.dump({"tables": {}, "sequences": {}}, f)
        if not os.path.exists(self.index_path):
            with open(self.index_path, 'w') as f:
                json.dump({}, f)

    async def _load_data(self):
        async with aiofiles.open(self.data_path, 'r') as f:
            return json.loads(await f.read())

    async def _save_data(self, data):
        async with aiofiles.open(self.data_path, 'w') as f:
            await f.write(json.dumps(data, separators=(',', ':')))

    async def create_table(self, table_name: str, schema: Dict[str, str]):
        async with self.lock:
            data = await self._load_data()
            if table_name not in data["tables"]:
                data["tables"][table_name] = {"schema": schema, "records": []}
                data["sequences"][table_name] = 0
                await self._save_data(data)

    async def insert(self, table_name: str, record: Dict[str, Any]) -> int:
        async with self.lock:
            data = await self._load_data()
            if table_name not in data["tables"]:
                raise ValueError(f"Table {table_name} not found")
            
            data["sequences"][table_name] += 1
            record_id = data["sequences"][table_name]
            record["id"] = record_id
            record["created_at"] = datetime.now().isoformat()
            
            data["tables"][table_name]["records"].append(record)
            await self._save_data(data)
            return record_id

    async def select(self, table_name: str, where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        data = await self._load_data()
        if table_name not in data["tables"]:
            return []
        
        records = data["tables"][table_name]["records"]
        if not where:
            return records
        
        return [r for r in records if all(r.get(k) == v for k, v in where.items())]

    async def select_one(self, table_name: str, where: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        records = await self.select(table_name, where)
        return records[0] if records else None

    async def update(self, table_name: str, where: Dict[str, Any], updates: Dict[str, Any]) -> int:
        async with self.lock:
            data = await self._load_data()
            if table_name not in data["tables"]:
                return 0
            
            updated_count = 0
            records = data["tables"][table_name]["records"]
            
            for record in records:
                if all(record.get(k) == v for k, v in where.items()):
                    record.update(updates)
                    record["updated_at"] = datetime.now().isoformat()
                    updated_count += 1
            
            if updated_count > 0:
                await self._save_data(data)
            return updated_count

    async def delete(self, table_name: str, where: Dict[str, Any]) -> int:
        async with self.lock:
            data = await self._load_data()
            if table_name not in data["tables"]:
                return 0
            
            records = data["tables"][table_name]["records"]
            original_count = len(records)
            
            data["tables"][table_name]["records"] = [
                r for r in records 
                if not all(r.get(k) == v for k, v in where.items())
            ]
            
            deleted_count = original_count - len(data["tables"][table_name]["records"])
            if deleted_count > 0:
                await self._save_data(data)
            return deleted_count

    async def backup(self, backup_path: str):
        data = await self._load_data()
        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        async with aiofiles.open(backup_path, 'w') as f:
            await f.write(json.dumps(backup_data, indent=2))

    async def restore(self, backup_path: str):
        async with aiofiles.open(backup_path, 'r') as f:
            backup_data = json.loads(await f.read())
        await self._save_data(backup_data["data"])

    def query(self, table_name: str) -> QueryBuilder:
        return QueryBuilder(table_name)
    
    async def aggregate(self, table_name: str, operation: str, field: str, 
                      where: Optional[Dict[str, Any]] = None) -> Any:
        records = await self.select(table_name, where)
        
        if operation == "count":
            return AggregationManager.count(records)
        elif operation == "sum":
            return AggregationManager.sum(records, field)
        elif operation == "avg":
            return AggregationManager.avg(records, field)
        elif operation == "min":
            return AggregationManager.min(records, field)
        elif operation == "max":
            return AggregationManager.max(records, field)
        else:
            raise ValueError(f"Unknown aggregation operation: {operation}")
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics.get_metrics()

    async def get_stats(self) -> Dict[str, Any]:
        data = await self._load_data()
        stats = {"tables": {}}
        for table_name, table_data in data["tables"].items():
            stats["tables"][table_name] = {
                "record_count": len(table_data["records"]),
                "next_id": data["sequences"][table_name] + 1
            }
        return stats