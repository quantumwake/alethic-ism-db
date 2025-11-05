import os
import logging as log

from ismcore.storage.processor_state_storage import FieldConfig
from psycopg2 import pool
from typing import List, Any, Dict, Optional, Callable, Union, Tuple

from ismdb.misc_utils import map_row_to_dict

logging = log.getLogger(__name__)

MIN_DB_CONNECTIONS = int(os.environ.get("MIN_DB_CONNECTIONS", 1))
MAX_DB_CONNECTIONS = int(os.environ.get("MAX_DB_CONNECTIONS", 5))


class SQLNull:
    """Marker class for explicit SQL NULL checks."""
    pass

class SQLNotNull:
    """Marker class for explicit SQL NOT NULL checks."""
    pass

class Condition:
    def __init__(self, operator: str, value: Any):
        self.operator = operator
        self.value = value


class BaseDatabaseAccess:

    def __init__(self, database_url, incremental: bool = False):
        self.database_url = database_url
        self.incremental = incremental

        if incremental:
            logging.warning(f'using incremental updates is not thread safe, '
                            f'please ensure to synchronize save_state(State) '
                            f'otherwise')

        # self.last_data_index = 0
        self.connection_pool = pool.SimpleConnectionPool(MIN_DB_CONNECTIONS, MAX_DB_CONNECTIONS, database_url)

    class SqlStatement:

        def __init__(self, sql: str, values: List[Any]):
            self.sql = sql
            self.values = values

    def create_connection(self):
        return self.connection_pool.getconn()

    def release_connection(self, conn):
        try:
            self.connection_pool.putconn(conn)
        except Exception as e:
            logging.error(f'failed to release connection as a result of {e}')

    def execute_delete_query(self, sql: str, conditions: Dict[str, Any]) -> int:
        conn = self.create_connection()
        params = []
        where_clauses = []
        for field, value in conditions.items():
            if value is not None:
                if value is SQLNull:
                    where_clauses.append(f"{field} IS NULL")
                else:
                    where_clauses.append(f"{field} = %s")
                    params.append(value)
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                affected_rows = cursor.rowcount
                conn.commit()
                return affected_rows
        except Exception as e:
            logging.error(f"Database delete query failed: {e}")
            raise
        finally:
            self.release_connection(conn)

    def execute_insert_query(self, table: str, insert_values: Dict[str, Any]) -> int:
        conn = self.create_connection()
        columns = []
        placeholders = []
        params = []

        for field, value in insert_values.items():
            if value is not None:
                columns.append(field)
                placeholders.append("%s")
                params.append(value)

        sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"

        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                conn.commit()
                return cursor.rowcount  # Number of rows inserted
        except Exception as e:
            logging.error(f"Database insert query failed: {e}")
            raise
        finally:
            self.release_connection(conn)

    def execute_update(self, table: str, update_values: dict, conditions: dict) -> int | None:
        conn = self.create_connection()
        set_clauses = []
        where_clauses = []
        params = []

        # Prepare SET clauses
        for field, value in update_values.items():
            set_clauses.append(f"{field} = %s")
            params.append(value)

        # Prepare WHERE clauses
        for field, value in conditions.items():
            if value is not None:
                if value is SQLNull:
                    where_clauses.append(f"{field} IS NULL")
                else:
                    where_clauses.append(f"{field} = %s")
                    params.append(value)

        # Construct the SQL statement
        sql = f"UPDATE {table} SET " + ", ".join(set_clauses)
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                affected_rows = cursor.rowcount
                conn.commit()
                return affected_rows
        except Exception as e:
            logging.error(f"Database update failed: {e}")
            raise
        finally:
            self.release_connection(conn)

    def execute_query_one(self, sql: str, conditions: dict, mapper: Callable) -> Optional[Any]:
        conn = self.create_connection()
        params = []
        where_clauses = []
        for field, value in conditions.items():
            if value is not None:
                if value is SQLNull:
                    where_clauses.append(f"{field} IS NULL")
                else:
                    where_clauses.append(f"{field} = %s")
                    params.append(value)
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                if rows:
                    if len(rows) > 1:
                        raise ValueError("Multiple rows returned when expecting a single value.")
                    return mapper(map_row_to_dict(cursor=cursor, row=rows[0]))
                else:
                    return None
        except Exception as e:
            logging.error(f"Database query failed: {e}")
            raise
        finally:
            self.release_connection(conn)

    from typing import Dict

    from typing import List, Callable, Optional, Any

    def execute_query_grouped(
            self,
            base_sql: str,
            conditions_and_grouping: List[FieldConfig],  # List of FieldConfig objects
            mapper: Callable[[Dict], Any]
    ) -> Optional[List[Any]]:
        """
        Generic function to execute SQL with dynamic SELECT, WHERE, and GROUP BY clauses,
        ensuring that all dynamic values are passed as parameters to prevent SQL injection.

        :param base_sql: The base SQL query before WHERE and GROUP BY clauses.
        :param conditions_and_grouping: List of FieldConfig objects defining field configurations.
        :param mapper: Function to map the result rows to the desired format.
        :return: Optional list of mapped results.
        """
        conn = self.create_connection()
        params = []
        where_clauses = []
        group_by_fields = []
        select_fields = []

        # Iterate through the conditions_and_grouping list to build WHERE, SELECT, and GROUP BY clauses
        for field_config in conditions_and_grouping:
            # Handle WHERE clause conditions
            if field_config.use_in_where and field_config.value is not None:
                where_clauses.append(f"{field_config.field_name} = %s")
                params.append(field_config.value)

            # Check if this field has an aggregate function
            aggregate = getattr(field_config, 'aggregate', None)

            if aggregate:
                # This is an aggregate field (e.g., SUM, MAX, AVG, COUNT)
                aggregate_upper = aggregate.upper()
                select_fields.append(f"{aggregate_upper}({field_config.field_name}) AS {field_config.field_name}")
            elif field_config.use_in_group_by:
                # This is a dimension field for grouping
                group_by_fields.append(field_config.field_name)
                select_fields.append(field_config.field_name)

        # Append WHERE clause to SQL
        if where_clauses:
            base_sql += " WHERE " + " AND ".join(where_clauses)

        # Construct the final SQL query
        final_sql = f"SELECT {', '.join(select_fields)} {base_sql}"

        if group_by_fields:
            final_sql += " GROUP BY " + ", ".join(group_by_fields)

        try:
            with conn.cursor() as cursor:
                cursor.execute(final_sql, params)  # Safe parameterized query execution
                rows = cursor.fetchall()
                results = [mapper(map_row_to_dict(cursor=cursor, row=row)) for row in rows]
                return results if results else None
        except Exception as e:
            logging.error(f"Database query failed: {e}")
            raise
        finally:
            self.release_connection(conn)

    def execute_query_many2(self,
                            sql: str,
                            conditions: Dict[str, Union[Any, Condition, Tuple[Any, Any]]],
                            mapper: Callable, order_by: [str] = None) \
            -> Optional[List[Any]]:
        """
        Execute a query with various comparison operators.

        Args:
            sql: Base SQL query
            conditions: Dictionary where:
                - key: field name
                - value can be:
                    - direct value (uses =)
                    - Condition object (for >, <, >=, <=)
                    - tuple of (min, max) for BETWEEN
                    - SQLNull for IS NULL
            mapper: Function to map results

        Example:
            conditions = {
                'age': Condition('>=', 18),
                'price': (100, 200),  # BETWEEN
                'status': 'active',   # equals
                'deleted_at': SQLNull # IS NULL
            }
            :param sql:
            :param sql:
            :param mapper:
            :param conditions:
            :param order_by:
        """
        conn = self.create_connection()
        params = []
        where_clauses = []

        for field, value in conditions.items():
            if value is not None:
                if value is SQLNull:
                    where_clauses.append(f"{field} IS NULL")
                elif isinstance(value, Condition):
                    where_clauses.append(f"{field} {value.operator} %s")
                    params.append(value.value)
                elif isinstance(value, tuple) and len(value) == 2:
                    where_clauses.append(f"{field} BETWEEN %s AND %s")
                    params.extend(value)
                else:
                    where_clauses.append(f"{field} = %s")
                    params.append(value)

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        if order_by:
            sql += f" ORDER BY " + ",".join(order_by)

        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                results = [mapper(map_row_to_dict(cursor=cursor, row=row)) for row in rows]
                if results:
                    return results
                else:
                    return None
        except Exception as e:
            logging.error(f"Database query failed: {e}")
            raise
        finally:
            self.release_connection(conn)

    def execute_query_many(self, sql: str, conditions: dict, mapper: Callable) -> Optional[List[Any]]:
        conn = self.create_connection()
        params = []
        where_clauses = []

        for field, value in conditions.items():
            if value is not None:
                if value is SQLNull:
                    where_clauses.append(f"{field} IS NULL")
                elif value is SQLNotNull:
                    where_clauses.append(f"{field} IS NOT NULL")
                else:
                    where_clauses.append(f"{field} = %s")
                    params.append(value)

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                results = [mapper(map_row_to_dict(cursor=cursor, row=row)) for row in rows]
                if results:
                    return results
                else:
                    return None
        except Exception as e:
            logging.error(f"Database query failed: {e}")
            raise
        finally:
            self.release_connection(conn)

    def execute_query_fixed(self, sql: str, params: Optional[List[Any]], mapper: Callable) -> Optional[List[Any]]:
        conn = self.create_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                if not rows:
                    return None

                results = [mapper(map_row_to_dict(cursor, row)) for row in rows]

            return results
        except Exception as e:
            logging.error(f"Database query failed: {e}")
            raise
        finally:
            self.release_connection(conn)


class BaseDatabaseAccessSinglePool(BaseDatabaseAccess):
    # Class-level dictionary to store connection pools
    _pools = {}

    def __init__(self, database_url, incremental: bool = False):
        self.database_url = database_url
        self.incremental = incremental

        # Use existing pool if available; otherwise, create and store a new one
        if database_url in BaseDatabaseAccessSinglePool._pools:
            self.connection_pool = BaseDatabaseAccessSinglePool._pools[database_url]
        else:
            logging.info(f"establishing connection pool for with max connections: {MAX_DB_CONNECTIONS}")
            if incremental:
                logging.warning(
                    'Using incremental updates is not thread-safe. '
                    'Please ensure to synchronize save_state(State) otherwise.'
                )
            self.connection_pool = pool.SimpleConnectionPool(
                MIN_DB_CONNECTIONS, MAX_DB_CONNECTIONS, database_url
            )
            BaseDatabaseAccessSinglePool._pools[database_url] = self.connection_pool

    def create_connection(self):
        try:
            conn = self.connection_pool.getconn()
            if conn is None:
                # Handle the case where no connection is available
                logging.error('No available connection in the pool.')
                raise Exception('No available connection in the pool.')
            return conn
        except Exception as e:
            logging.error(f'Failed to create a connection: {e}')
            raise

    def release_connection(self, conn):
        try:
            # Check if the connection is valid before returning it to the pool
            if conn:
                self.connection_pool.putconn(conn)
            else:
                logging.warning('Attempted to release a null connection.')
        except Exception as e:
            logging.error(f'Failed to release connection: {e}')
            # Optionally, you might want to close the connection if it cannot be returned
            if conn:
                conn.close()

