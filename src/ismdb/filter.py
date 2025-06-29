import logging as log
import datetime as dt
import uuid
import json
from typing import Optional, List, Dict, Any

from ismcore.storage.processor_state_storage import FilterStorage
from ismcore.model.filter import Filter, FilterItem, FilterOperator
from ismdb.base import BaseDatabaseAccessSinglePool

logging = log.getLogger(__name__)


class FilterDatabaseStorage(FilterStorage, BaseDatabaseAccessSinglePool):

    def insert_filter(self, filter: Filter) -> Filter:
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                if not filter.id:
                    filter.id = str(uuid.uuid4())

                sql = """
                    INSERT INTO filter (id, name, user_id, filter_items, created_date) 
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) 
                    DO UPDATE SET 
                        name = EXCLUDED.name,
                        filter_items = EXCLUDED.filter_items
                """
                
                # Convert filter_items to JSON string for storage
                filter_items_json = json.dumps({
                    key: {
                        'key': item.key,
                        'operator': item.operator.value if hasattr(item.operator, 'value') else item.operator,
                        'value': item.value
                    } for key, item in filter.filter_items.items()
                }) if filter.filter_items else '{}'

                values = [
                    filter.id,
                    filter.name,
                    filter.user_id,
                    filter_items_json,
                    dt.datetime.utcnow()
                ]
                cursor.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

        return filter

    def fetch_filter(self, filter_id: str) -> Optional[Filter]:
        filters = self.execute_query_many(
            sql="select * from filter",
            conditions={"id": filter_id},
            mapper=lambda row: self._map_row_to_filter(row)
        )
        return filters[0] if filters else None

    def fetch_filters_by_user(self, user_id: str) -> Optional[List[Filter]]:
        filters = self.execute_query_many(
            sql="select * from filter",
            conditions={"user_id": user_id},
            mapper=lambda row: self._map_row_to_filter(row)
        )
        return filters

    def delete_filter(self, filter_id: str) -> int:
        conn = self.create_connection()
        rows_deleted = 0

        try:
            with conn.cursor() as cursor:
                sql = "DELETE FROM filter WHERE id = %s"
                cursor.execute(sql, [filter_id])
                rows_deleted = cursor.rowcount
            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

        return rows_deleted

    def apply_filter_on_data(self, filter_id: str, data: Dict[str, Any]) -> bool:
        filter = self.fetch_filter(filter_id)
        if not filter:
            return False
        
        return filter.apply_filter_on_data(data)

    def _map_row_to_filter(self, row) -> Filter:
        filter_items = row['filter_items'] if row.get('filter_items') else {}

        return Filter(
            id=row['id'],
            name=row.get('name'),
            filter_items=filter_items,
            user_id=row.get('user_id')
        )