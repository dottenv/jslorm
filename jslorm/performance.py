from typing import Dict, Any, List, Optional, Type, Union
from datetime import datetime
import hashlib
import json

class IndexManager:
    def __init__(self):
        self.indexes: Dict[str, Dict[str, Dict[str, List[int]]]] = {}

    def create_index(self, table_name: str, field_name: str):
        if table_name not in self.indexes:
            self.indexes[table_name] = {}
        if field_name not in self.indexes[table_name]:
            self.indexes[table_name][field_name] = {}

    def add_to_index(self, table_name: str, field_name: str, value: Any, record_id: int):
        self.create_index(table_name, field_name)
        str_value = str(value)
        if str_value not in self.indexes[table_name][field_name]:
            self.indexes[table_name][field_name][str_value] = []
        if record_id not in self.indexes[table_name][field_name][str_value]:
            self.indexes[table_name][field_name][str_value].append(record_id)

    def remove_from_index(self, table_name: str, field_name: str, value: Any, record_id: int):
        if (table_name in self.indexes and 
            field_name in self.indexes[table_name] and 
            str(value) in self.indexes[table_name][field_name]):
            try:
                self.indexes[table_name][field_name][str(value)].remove(record_id)
            except ValueError:
                pass

    def find_by_index(self, table_name: str, field_name: str, value: Any) -> List[int]:
        if (table_name in self.indexes and 
            field_name in self.indexes[table_name] and 
            str(value) in self.indexes[table_name][field_name]):
            return self.indexes[table_name][field_name][str(value)].copy()
        return []

class CacheManager:
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Any] = {}
        self.access_times: Dict[str, datetime] = {}
        self.max_size = max_size

    def _generate_key(self, table_name: str, query: Dict[str, Any]) -> str:
        query_str = json.dumps(query, sort_keys=True)
        return hashlib.md5(f"{table_name}:{query_str}".encode()).hexdigest()

    def get(self, table_name: str, query: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        key = self._generate_key(table_name, query)
        if key in self.cache:
            self.access_times[key] = datetime.now()
            return self.cache[key]
        return None

    def set(self, table_name: str, query: Dict[str, Any], result: List[Dict[str, Any]]):
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        
        key = self._generate_key(table_name, query)
        self.cache[key] = result
        self.access_times[key] = datetime.now()

    def invalidate_table(self, table_name: str):
        keys_to_remove = [k for k in self.cache.keys() if k.startswith(f"{table_name}:")]
        for key in keys_to_remove:
            del self.cache[key]
            del self.access_times[key]

    def _evict_oldest(self):
        if not self.access_times:
            return
        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[oldest_key]
        del self.access_times[oldest_key]

class CompressionManager:
    @staticmethod
    def compress_data(data: str) -> bytes:
        import gzip
        return gzip.compress(data.encode('utf-8'))

    @staticmethod
    def decompress_data(compressed_data: bytes) -> str:
        import gzip
        return gzip.decompress(compressed_data).decode('utf-8')

class AggregationManager:
    @staticmethod
    def count(records: List[Dict[str, Any]]) -> int:
        return len(records)

    @staticmethod
    def sum(records: List[Dict[str, Any]], field: str) -> Union[int, float]:
        total = 0
        for record in records:
            value = record.get(field, 0)
            if isinstance(value, (int, float)):
                total += value
        return total

    @staticmethod
    def avg(records: List[Dict[str, Any]], field: str) -> float:
        if not records:
            return 0.0
        total = AggregationManager.sum(records, field)
        return total / len(records)

    @staticmethod
    def min(records: List[Dict[str, Any]], field: str) -> Any:
        if not records:
            return None
        values = [r.get(field) for r in records if r.get(field) is not None]
        return min(values) if values else None

    @staticmethod
    def max(records: List[Dict[str, Any]], field: str) -> Any:
        if not records:
            return None
        values = [r.get(field) for r in records if r.get(field) is not None]
        return max(values) if values else None