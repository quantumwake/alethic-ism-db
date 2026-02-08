import json
import logging as log
from typing import Optional, List, Dict, Any

from ismcore.model.base_model import ProcessorState, ProcessorStateDirection, ProcessorStatusCode, EdgeFunctionConfig
from ismcore.storage.processor_state_storage import ProcessorStateRouteStorage

from ismdb.base import BaseDatabaseAccessSinglePool

logging = log.getLogger(__name__)


class ProcessorStateDatabaseStorage(ProcessorStateRouteStorage, BaseDatabaseAccessSinglePool):

    # def fetch_prcoessor_state_details(self, processor_id, state_id, direction: ProcessorStateDirection, provider_id):
    #     return self.execute_query_many(
    #         sql="""select ps.processor_id,
    #                    ps.state_id,
    #                    ps.direction,
    #                    ps.count,
    #                    ps.current_index,
    #                    ps.maximum_index,
    #                    ps.status as state_status
    #                    p.project_id,
    #                    p.provider_id
    #               from processor_state ps
    #              inner join processor p
    #                 on p.id = ps.processor_id""",
    #         conditions={
    #             'processor_id': processor_id,
    #             'state_id': state_id,
    #             'direction': direction.value if direction else None
    #         },
    #         mapper=lambda row: ProcessorStateDetail(**row))

    def fetch_processor_state_routes_by_project_id(self, project_id) -> Optional[List[ProcessorState]]:
        """
        Fetch all processor state routes associated with a project.

        Args:
            project_id: The project ID to filter by

        Returns:
            List of ProcessorState objects for the project, or None if not found
        """
        processor_states = self.execute_query_fixed(
            sql="""
                SELECT * FROM processor_state 
                 WHERE state_id IN (
                    SELECT id FROM state 
                     WHERE project_id = %s
                 )""",
            params=[project_id],
            mapper=lambda row: ProcessorState(**row)
        )

        return processor_states

    def fetch_processor_state_route_by_route_id(self, route_id: str) -> Optional[ProcessorState]:
        """
        Fetch a single processor state route by its route ID.

        Args:
            route_id: The unique route identifier

        Returns:
            The ProcessorState object if found, None otherwise

        Raises:
            ValueError: If more than one route is found (indicates storage implementation issue)
        """
        forward_processor_state = self.fetch_processor_state_route(route_id=route_id)

        # more than one route found, this must be a storage class implementation issue
        if forward_processor_state and len(forward_processor_state) > 1:
            raise ValueError(f'returned too many routes for given {route_id}, there is a problem with the '
                             f'underlying storage class implementation {type(self)}')

        # fetch the first processor state (aka route
        return forward_processor_state[0] if forward_processor_state else None

    def fetch_processor_state_route(self,
                                    route_id: str = None,
                                    processor_id: str = None,
                                    state_id: str = None,
                                    direction: ProcessorStateDirection = None,
                                    status: ProcessorStatusCode = None) \
            -> Optional[List[ProcessorState]]:
        """
        Fetch processor state routes matching the given criteria.

        All parameters are optional and act as filters. Only non-None parameters
        are included in the WHERE clause.

        Args:
            route_id: Filter by route ID
            processor_id: Filter by processor ID
            state_id: Filter by state ID
            direction: Filter by direction (INPUT/OUTPUT)
            status: Filter by status code

        Returns:
            List of matching ProcessorState objects, or None if not found
        """
        return self.execute_query_many(
            sql="SELECT * FROM processor_state",
            conditions={
                'id': route_id,
                'processor_id': processor_id,
                'state_id': state_id,
                'direction': direction.value if direction else None,
                'status': status.value if status else None
            },
            mapper=lambda row: ProcessorState(**row))

    def delete_processor_state_route_by_id(self, processor_state_id: str) -> int:
        """
        Delete a processor state route by its ID.

        Args:
            processor_state_id: The ID of the processor state route to delete

        Returns:
            Number of rows deleted (0 or 1)
        """
        return self.execute_delete_query(
            "DELETE FROM processor_state",
            conditions={
                "id": processor_state_id
            }
        )

    def delete_processor_state_route(self, route_id: str) -> int:
        """
        Delete a processor state route by its route ID.

        Args:
            route_id: The route ID to delete

        Returns:
            Number of rows deleted (0 or 1)
        """
        return self.execute_delete_query(
            "DELETE FROM processor_state",
            conditions={
                "id": route_id
            }
        )

    def delete_processor_state_routes_by_state_id(self, state_id: str) -> int:
        """
        Delete all processor state routes associated with a state.

        Args:
            state_id: The state ID whose routes should be deleted

        Returns:
            Number of rows deleted
        """
        return self.execute_delete_query(
            "DELETE FROM processor_state",
            conditions={
                "state_id": state_id
            }
        )

    def insert_processor_state_route(self, processor_state: ProcessorState) \
            -> ProcessorState:
        """
        Insert or update a processor state route (upsert).

        Uses PostgreSQL ON CONFLICT to perform an upsert on the composite key
        (processor_id, state_id, direction). On conflict, updates count, status,
        current_index, maximum_index, and edge_function.

        WARNING: This method updates ALL mutable fields on conflict. If you only
        need to update the status, use update_processor_state_route_status() instead
        to avoid overwriting other fields like edge_function.

        Args:
            processor_state: The ProcessorState object to insert/update

        Returns:
            The ProcessorState with internal_id populated from the database
        """
        try:
            conn = self.create_connection()
            with (conn.cursor() as cursor):
                sql = """
                    INSERT INTO processor_state (
                        id,
                        processor_id,
                        state_id,
                        direction,
                        status,
                        count,
                        current_index,
                        maximum_index,
                        edge_function
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (processor_id, state_id, direction)
                    DO UPDATE SET
                        count = EXCLUDED.count,
                        status = EXCLUDED.status,
                        current_index = EXCLUDED.current_index,
                        maximum_index = EXCLUDED.maximum_index,
                        edge_function = EXCLUDED.edge_function
                    RETURNING internal_id
                """

                edge_function_json = processor_state.edge_function.model_dump_json() \
                    if processor_state.edge_function else None

                cursor.execute(sql, [
                    processor_state.id,
                    processor_state.processor_id,
                    processor_state.state_id,
                    processor_state.direction.value,
                    processor_state.status.value,
                    processor_state.count,
                    processor_state.current_index,
                    processor_state.maximum_index,
                    edge_function_json
                ])

                # fetch the internal id from the response of the executed statement
                processor_state.internal_id = cursor.fetchone()[0] \
                    if not processor_state.internal_id \
                    else processor_state.internal_id

            conn.commit()
            return processor_state
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def update_processor_state_route_status(self, route_id: str, status: ProcessorStatusCode) -> int:
        """
        Update only the status field of a processor state route.

        This method should be used when you only need to change the status without
        affecting other fields like edge_function, count, current_index, etc.

        Args:
            route_id: The route ID to update
            status: The new status to set

        Returns:
            Number of rows affected (0 or 1)
        """
        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE processor_state SET status = %s WHERE id = %s",
                    [status.value, route_id]
                )
                row_count = cursor.rowcount
            conn.commit()
            return row_count
        except Exception as e:
            logging.error(f"Failed to update processor state route status: {e}")
            raise e
        finally:
            self.release_connection(conn)

    def fetch_edge_function_config(self, route_id: str) -> Optional[EdgeFunctionConfig]:
        """Fetch edge function configuration for a processor state route."""
        result = self.execute_query_fixed(
            sql="SELECT edge_function FROM processor_state WHERE id = %s",
            params=[route_id],
            mapper=lambda row: row.get('edge_function')
        )

        if result and result[0]:
            edge_function_data = result[0]
            if isinstance(edge_function_data, str):
                edge_function_data = json.loads(edge_function_data)
            return EdgeFunctionConfig(**edge_function_data)
        return None

    def update_edge_function_config(self, route_id: str, config: EdgeFunctionConfig) -> Optional[EdgeFunctionConfig]:
        """Update edge function configuration for a processor state route."""
        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                config_json = config.model_dump_json() if config else None
                cursor.execute(
                    "UPDATE processor_state SET edge_function = %s WHERE id = %s RETURNING edge_function",
                    [config_json, route_id]
                )
                result = cursor.fetchone()
            conn.commit()

            if result and result[0]:
                return EdgeFunctionConfig(**result[0])
            return config
        except Exception as e:
            logging.error(f"Failed to update edge function config: {e}")
            raise e
        finally:
            self.release_connection(conn)
