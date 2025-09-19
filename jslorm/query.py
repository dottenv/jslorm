from typing import Dict, Any, List, Optional, Union
from enum import Enum

class Operator(str, Enum):
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    LIKE = "like"
    ILIKE = "ilike"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"

class QueryBuilder:
    def __init__(self, table_name: str):
        self.table_name = table_name
        self._where_conditions = []
        self._order_by = []
        self._limit_value = None
        self._offset_value = None
        self._select_fields = None

    def where(self, field: str, operator: Union[str, Operator], value: Any = None):
        if isinstance(operator, str):
            operator = Operator(operator)
        
        condition = {"field": field, "operator": operator, "value": value}
        self._where_conditions.append(condition)
        return self

    def order_by(self, field: str, desc: bool = False):
        self._order_by.append({"field": field, "desc": desc})
        return self

    def limit(self, count: int):
        self._limit_value = count
        return self

    def offset(self, count: int):
        self._offset_value = count
        return self

    def select(self, fields: List[str]):
        self._select_fields = fields
        return self

    def _match_condition(self, record: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        field = condition["field"]
        operator = condition["operator"]
        value = condition["value"]
        record_value = record.get(field)

        if operator == Operator.EQ:
            return record_value == value
        elif operator == Operator.NE:
            return record_value != value
        elif operator == Operator.GT:
            return record_value is not None and record_value > value
        elif operator == Operator.GTE:
            return record_value is not None and record_value >= value
        elif operator == Operator.LT:
            return record_value is not None and record_value < value
        elif operator == Operator.LTE:
            return record_value is not None and record_value <= value
        elif operator == Operator.IN:
            return record_value in value
        elif operator == Operator.NOT_IN:
            return record_value not in value
        elif operator == Operator.LIKE:
            return isinstance(record_value, str) and value.lower() in record_value.lower()
        elif operator == Operator.ILIKE:
            return isinstance(record_value, str) and value.lower() in record_value.lower()
        elif operator == Operator.IS_NULL:
            return record_value is None
        elif operator == Operator.IS_NOT_NULL:
            return record_value is not None
        return False

    def apply_filters(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Применяем WHERE условия
        filtered = records
        for condition in self._where_conditions:
            filtered = [r for r in filtered if self._match_condition(r, condition)]

        # Применяем ORDER BY
        if self._order_by:
            for order in reversed(self._order_by):
                field = order["field"]
                desc = order["desc"]
                filtered.sort(key=lambda x: x.get(field, ""), reverse=desc)

        # Применяем OFFSET и LIMIT
        if self._offset_value:
            filtered = filtered[self._offset_value:]
        if self._limit_value:
            filtered = filtered[:self._limit_value]

        # Применяем SELECT полей
        if self._select_fields:
            filtered = [{k: v for k, v in record.items() if k in self._select_fields} 
                       for record in filtered]

        return filtered

    def to_dict(self) -> Dict[str, Any]:
        return {
            "where": self._where_conditions,
            "order_by": self._order_by,
            "limit": self._limit_value,
            "offset": self._offset_value,
            "select": self._select_fields
        }