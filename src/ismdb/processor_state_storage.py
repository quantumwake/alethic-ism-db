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
        # fetch the processors to forward the state query to
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
        return self.execute_delete_query(
            "DELETE FROM processor_state",
            conditions={
                "id": processor_state_id
            }
        )

    def delete_processor_state_route(self, route_id: str) -> int:
        return self.execute_delete_query(
            "DELETE FROM processor_state",
            conditions={
                "id": route_id
            }
        )

    def delete_processor_state_routes_by_state_id(self, state_id: str) -> int:
        return self.execute_delete_query(
            "DELETE FROM processor_state",
            conditions={
                "state_id": state_id
            }
        )

    def insert_processor_state_route(self, processor_state: ProcessorState) \
            -> ProcessorState:

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
