import uuid

from psycopg2 import pool
from typing import List, Any, Dict, Optional, Callable
import logging as log

# import state and other models
from core.base_model import (
    ProcessorStateDirection,
    UserProject,
    UserProfile,
    WorkflowNode,
    WorkflowEdge, ProcessorProperty, ProcessorStateDetail, ProcessorStatusCode, MonitorLogEvent
)

from core.processor_state import (
    State,
    StateDataKeyDefinition,
    StateConfigLM,
    StateConfig,
    StateDataColumnDefinition,
    StateDataRowColumnData,
    StateDataColumnIndex,
    InstructionTemplate, StateConfigCode, StateConfigVisual
)

# import interfaces relevant to the storage subsystem
from core.processor_state_storage import (
    Processor,
    ProcessorState,
    ProcessorProvider,
    ProcessorStorage,
    StateStorage,
    ProcessorProviderStorage,
    ProcessorStateRouteStorage,
    TemplateStorage,
    WorkflowStorage,
    UserProjectStorage,
    UserProfileStorage, MonitorLogEventStorage, StateMachineStorage
)

from .misc_utils import create_state_id_by_state, map_row_to_dict, map_rows_to_dicts

logging = log.getLogger(__name__)


class SQLNull:
    """Marker class for explicit SQL NULL checks."""
    pass


class BaseDatabaseAccess:

    def __init__(self, database_url, incremental: bool = False):
        self.database_url = database_url
        self.incremental = incremental

        if incremental:
            logging.warning(f'using incremental updates is not thread safe, '
                            f'please ensure to synchronize save_state(State) '
                            f'otherwise')

        # self.last_data_index = 0
        self.connection_pool = pool.SimpleConnectionPool(1, 10, database_url)

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

    def execute_update(self, table: str, update_values: dict, conditions: dict) -> int:
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

    def execute_query_many(self, sql: str, conditions: dict, mapper: Callable) -> Optional[List[Any]]:
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


class UserProfileDatabaseStorage(UserProfileStorage, BaseDatabaseAccess):

    def insert_user_profile(self, user_profile: UserProfile):
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:

                sql = """
                    INSERT INTO user_profile (user_id) 
                    VALUES (%s)
                    ON CONFLICT (user_id) 
                    DO NOTHING
                """

                values = [
                    user_profile.user_id
                ]
                cursor.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

        return user_profile


class UserProjectDatabaseStorage(UserProjectStorage, BaseDatabaseAccess):

    def delete_user_project(self, project_id):
        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = """DELETE FROM user_project WHERE project_id = %s"""
                cursor.execute(sql, [project_id])
            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def fetch_user_project(self, project_id: str) -> Optional[UserProject]:
        return self.execute_query_one(
            "select * from user_project",
            conditions={
                "project_id": project_id
            },
            mapper=lambda row: UserProject(**row)
        )

    def insert_user_project(self, user_project: UserProject):
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:

                sql = """
                    INSERT INTO user_project (project_id, project_name, user_id) 
                    VALUES (%s, %s, %s)
                    ON CONFLICT (project_id) 
                    DO UPDATE SET project_name = EXCLUDED.project_name
                """

                # assign project id if project id is not assigned
                user_project.project_id = user_project.project_id if user_project.project_id else str(uuid.uuid4())

                values = [
                    user_project.project_id,
                    user_project.project_name,
                    user_project.user_id
                ]
                cursor.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

        return user_project

    def fetch_user_projects(self, user_id: str) -> List[UserProject]:
        return self.execute_query_many(
            "select * from user_project",
            conditions={
                "user_id": user_id
            },
            mapper=lambda row: UserProject(**row)
        )


class WorkflowDatabaseStorage(WorkflowStorage, BaseDatabaseAccess):

    def delete_workflow_node(self, node_id):
        return self.execute_delete_query(
            sql="DELETE FROM workflow_node",
            conditions={"node_id": node_id}
        )

    def fetch_workflow_nodes(self, project_id: str) -> Optional[List[WorkflowNode]]:
        return self.execute_query_many(
            "select * from workflow_node",
            conditions={
                "project_id": project_id
            },
            mapper=lambda row: WorkflowNode(**row)
        )

    def insert_workflow_node(self, node: WorkflowNode) -> WorkflowNode:
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:

                sql = """
                           INSERT INTO workflow_node (
                                node_id, 
                                node_type, 
                                node_label, 
                                project_id, 
                                object_id, 
                                position_x, 
                                position_y, 
                                width, 
                                height)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (node_id) 
                           DO UPDATE SET 
                            node_label = EXCLUDED.node_label,
                            object_id=EXCLUDED.object_id,
                            node_type=EXCLUDED.node_type,
                            position_x=EXCLUDED.position_x,
                            position_y=EXCLUDED.position_y,
                            width=EXCLUDED.width,
                            height=EXCLUDED.height
                       """

                values = [
                    node.node_id,
                    node.node_type,
                    node.node_label,
                    node.project_id,
                    node.object_id,  # the actual object id used, based on the type of node this is
                    node.position_x,
                    node.position_y,
                    node.width,
                    node.height
                ]
                cursor.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

        return node

    def delete_workflow_edge(self, source_node_id: str, target_node_id: str):
        return self.execute_delete_query(
            sql="DELETE FROM workflow_edge",
            conditions={
                "source_node_id": source_node_id,
                "target_node_id": target_node_id
            }
        )

    def fetch_workflow_edges(self, project_id: str) -> Optional[List[WorkflowEdge]]:
        sql = """
                SELECT * FROM workflow_edge
                WHERE source_node_id IN (
                    SELECT node_id FROM workflow_node WHERE project_id = %s
                )
                OR target_node_id IN (
                    SELECT node_id FROM workflow_node WHERE project_id = %s
                )
            """
        params = [project_id, project_id]
        return self.execute_query_fixed(sql, params, lambda row: WorkflowEdge(**row))

    def insert_workflow_edge(self, edge: WorkflowEdge) -> WorkflowEdge:
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:

                sql = """
                           INSERT INTO workflow_edge (
                            source_node_id, 
                            target_node_id, 
                            source_handle, 
                            target_handle, 
                            animated, 
                            edge_label,
                            type)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (source_node_id, target_node_id) 
                           DO UPDATE SET 
                            animated = EXCLUDED.animated,
                            edge_label = EXCLUDED.edge_label
                       """

                values = [
                    edge.source_node_id,
                    edge.target_node_id,
                    edge.source_handle,
                    edge.target_handle,
                    edge.animated,
                    edge.edge_label,
                    edge.type
                ]
                cursor.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

        return edge


class ProcessorProviderDatabaseStorage(ProcessorProviderStorage, BaseDatabaseAccess):

    def fetch_processor_provider(self, id: str) -> Optional[ProcessorProvider]:
        return self.execute_query_one(
            sql="select * from processor_provider",
            conditions={
                "id": id
            },
            mapper=lambda row: ProcessorProvider(**row)
        )

    def fetch_processor_providers(self,
                                  name: str = None,
                                  version: str = None,
                                  class_name: str = None,
                                  user_id: str = None,
                                  project_id: str = None) -> Optional[List[ProcessorProvider]]:

        return self.execute_query_many(
            sql="SELECT * FROM processor_provider",
            conditions={
                'name': name,
                'version': version,
                'class_name': class_name,
                'user_id': user_id,
                'project_id': project_id
            },
            mapper=lambda row: ProcessorProvider(**row))

    def insert_processor_provider(self, provider: ProcessorProvider) -> ProcessorProvider:
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = """
                          MERGE INTO processor_provider AS target
                          USING (SELECT 
                                   %s AS id, 
                                   %s AS name, 
                                   %s AS version, 
                                   %s AS class_name,
                                   %s AS user_id,
                                   %s AS project_id) AS source
                             ON target.id = source.id 
                          WHEN MATCHED THEN 
                              UPDATE SET 
                                name = source.name, 
                                version = source.version,
                                class_name = source.class_name
                          WHEN NOT MATCHED THEN 
                              INSERT (id, name, version, class_name, user_id, project_id)
                              VALUES (
                                   source.id, 
                                   source.name, 
                                   source.version, 
                                   source.class_name,
                                   source.user_id,
                                   source.project_id
                              )
                      """

                provider.id = provider.id if provider.id else str(uuid.uuid4())

                cursor.execute(sql, [
                    provider.id,
                    provider.name,
                    provider.version,
                    provider.class_name,
                    provider.user_id,
                    provider.project_id
                ])

                conn.commit()
                return provider
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def delete_processor_provider(self, user_id: str, provider_id: str, project_id: str = None) -> int:
        conn = self.create_connection()

        if not user_id:
            raise Exception('Illegal operations, user_id is mandatory when deleting providers')

        try:
            with conn.cursor() as cursor:

                # user_id is mandatory, cannot delete system level providers
                sql = """
                    DELETE FROM processor_provider 
                     WHERE id = %s 
                       AND user_id=%s
                """

                if project_id:
                    # delete provider with user_id, project_id and provider_idd
                    sql = f"{sql} AND project_id=%s"
                    cursor.execute(sql, [provider_id, user_id, project_id])
                else:
                    # delete provider only with user_id and provider_id
                    cursor.execute(sql, [provider_id, user_id])

                count = cursor.rowcount  # Get the number of rows deleted
                conn.commit()
                return count  # Return the count of deleted rows
        except Exception as e:
            logging.error(e)
            raise e

        finally:
            self.release_connection(conn)


class TemplateDatabaseStorage(TemplateStorage, BaseDatabaseAccess):

    def fetch_templates(self, project_id: str = None) -> Optional[List[InstructionTemplate]]:
        return self.execute_query_many(
            sql="SELECT * FROM template",
            conditions={
                'project_id': project_id
            },
            mapper=lambda row: InstructionTemplate(**row))

    def fetch_template(self, template_id: str) -> InstructionTemplate:
        return self.execute_query_one(
            sql="SELECT * FROM template",
            conditions={
                'template_id': template_id
            },
            mapper=lambda row: InstructionTemplate(**row))

    def delete_template(self, template_id):
        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = """DELETE FROM template WHERE template_id = %s"""
                cursor.execute(sql, [template_id])
            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def insert_template(self, template: InstructionTemplate = None) -> InstructionTemplate:

        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = """
                          MERGE INTO template AS target
                          USING (SELECT 
                                   %s AS template_id, 
                                   %s AS template_path, 
                                   %s AS template_content, 
                                   %s AS template_type,
                                   %s AS project_id) AS source
                             ON target.template_id = source.template_id 
                          WHEN MATCHED THEN 
                              UPDATE SET 
                                template_path = source.template_path, 
                                template_content = source.template_content
                          WHEN NOT MATCHED THEN 
                              INSERT (template_id, template_path, template_content, template_type, project_id)
                              VALUES (
                                   source.template_id, 
                                   source.template_path, 
                                   source.template_content, 
                                   source.template_type,
                                   source.project_id
                              )
                      """

                # create a template id if it is not specified
                template.template_id = template.template_id if template.template_id else str(uuid.uuid4())

                values = [
                    template.template_id,
                    template.template_path,
                    template.template_content,
                    template.template_type,
                    template.project_id
                ]
                cursor.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

        return template


class ProcessorDatabaseStorage(ProcessorStorage, BaseDatabaseAccess):

    def fetch_processors(self, provider_id: str = None, project_id: str = None) -> List[Processor]:
        processors = self.execute_query_many(
            sql="SELECT * FROM processor",
            conditions={
                'project_id': project_id,
                'provider_id': provider_id
            },
            mapper=lambda row: Processor(**row))

        for p in processors:
            p.properties = self.fetch_processor_properties(processor_id=p.id)

        return processors

    def fetch_processor(self, processor_id: str) -> Optional[Processor]:
        processor = self.execute_query_one(
            sql="SELECT * FROM processor",
            conditions={
                'id': processor_id
            },
            mapper=lambda row: Processor(**row))

        if processor:
            processor.properties = self.fetch_processor_properties(processor_id=processor_id)

        return processor

    def change_processor_status(self, processor_id: str, status: ProcessorStatusCode) -> int:
        if not processor_id:
            raise ValueError(f'processor id cannot be empty or null')

        return self.execute_update(
            table="processor",
            update_values={
                "status": status.value
            },
            conditions={
                "id": processor_id
            }
        )

    def insert_processor(self, processor: Processor) -> Processor:

        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = f"""
                    INSERT INTO processor (id, provider_id, project_id, status)
                         VALUES (%s, %s, %s, %s)
                             ON CONFLICT (id) 
                      DO UPDATE SET 
                        provider_id = EXCLUDED.provider_id
--                         status = EXCLUDED.status
                """

                processor.id = processor.id if processor.id else str(uuid.uuid4())

                cursor.execute(sql, [
                    processor.id,
                    processor.provider_id,
                    processor.project_id,
                    processor.status.value
                ])

                conn.commit()
            return processor
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def fetch_processor_properties(self, processor_id: str, name: str = None) -> Optional[List[ProcessorProperty]]:
        return self.execute_query_many(
            sql="SELECT * FROM processor_property",
            conditions={
                'processor_id': processor_id,
                'name': name
            },
            mapper=lambda row: ProcessorProperty(**row))

    def fetch_processor_property_by_name(self, processor_id: str, property_name: str):
        return self.execute_query_one(
            sql="SELECT * FROM processor_property",
            conditions={
                'processor_id': processor_id,
                'name': property_name
            },
            mapper=lambda row: ProcessorProperty(**row)
        )

    def update_processor_property(self, processor_id: str, property_name: str, property_value: str) -> int:
        return self.execute_update(
            table="processor_property",
            update_values={
                "value": property_value
            },
            conditions={
                'processor_id': processor_id,
                'name': property_name
            },
        )

    def insert_processor_properties(self, properties: List[ProcessorProperty]) -> List[ProcessorProperty]:
        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = f"""
                    INSERT INTO processor_property (processor_id, name, value)
                         VALUES (%s, %s, %s)
                             ON CONFLICT (processor_id, name) 
                      DO UPDATE SET 
                           value = EXCLUDED.value
                """

                for property in properties:
                    cursor.execute(sql, [
                        property.processor_id,
                        property.name,
                        property.value
                    ])

                conn.commit()
            return properties
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def delete_processor_property(self, processor_id: str, name: str) -> int:
        return self.execute_delete_query(
            sql="DELETE FROM processor_property",
            conditions={
                'processor_id': processor_id,
                'name': name
            }
        )


class StateDatabaseStorage(StateStorage, BaseDatabaseAccess):

    def fetch_state_data_by_column_id(self, column_id: int) -> Optional[StateDataRowColumnData]:
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""
                    select * from state_column_data 
                    where column_id = %s order by data_index
                """

                cursor.execute(sql, [column_id])
                rows = cursor.fetchall()
                values = [row[2] for row in rows]
                data = StateDataRowColumnData(
                    values=values,
                    count=len(values)
                )

            return data
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def fetch_state_columns(self, state_id: str) \
            -> Optional[Dict[str, StateDataColumnDefinition]]:
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""select * from state_column where state_id = %s"""
                cursor.execute(sql, [state_id])
                rows = cursor.fetchall()
                results = map_rows_to_dicts(cursor, rows)
                results = {row['name']: row for row in results if row['name']}

                columns = {
                    column: StateDataColumnDefinition.model_validate(column_definition)
                    for column, column_definition in results.items()
                }
            return columns
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def fetch_states(self, project_id: str = None, state_type: str = None) -> Optional[List[State]]:

        return self.execute_query_many(
            sql="SELECT * FROM state",
            conditions={
                'project_id': project_id,
                'state_type': state_type
            },
            mapper=lambda row: State(**row))

    def fetch_state(self, state_id: str) -> Optional[State]:
        return self.execute_query_one(
            sql="SELECT * FROM state",
            conditions={
                'id': state_id
            },
            mapper=lambda row: State(**row))


    def insert_state(self, state: State, config_uuid=False):
        conn = self.create_connection()

        # get the configuration type for this state based on the configuration setup
        if config_uuid:
            state.id = create_state_id_by_state(state=state)
        else:
            state.id = state.id if state.id else str(uuid.uuid4())

        try:
            with conn.cursor() as cursor:

                sql = """
                    INSERT INTO state (id, project_id, state_type) 
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) 
                    DO UPDATE SET 
                        state_type = EXCLUDED.state_type
                """

                # setup data values for state
                values = [
                    state.id,
                    state.project_id,
                    state.state_type
                ]

                cursor.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

        return state

    def fetch_state_config(self, state_id: str):

        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""
                select * from state_config where state_id = %s 
                """
                cursor.execute(sql, [state_id])
                rows = cursor.fetchall()
                results = map_rows_to_dicts(cursor, rows) if rows else {}

                if results:
                    results = {
                        attribute['attribute']: attribute['data']
                        for attribute in results
                    }

            return results
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def insert_state_config(self, state: State) -> State:

        # switch it to a database storage class
        attributes = [
            {
                "name": attr_name,
                "data": attr_value
            }
            for attr_name, attr_value in vars(state.config).items()
            if isinstance(attr_value, (int, float, str, bool, bytes, complex))
        ]

        # create a new state
        state_id = create_state_id_by_state(state=state)

        if not attributes:
            logging.info(f'no additional attributes specified for '
                         f'state_id: {state_id}, name: {state.config.name}, '
                         f'version: {state.config.version}')
            return state

        conn = self.create_connection()

        try:

            with conn.cursor() as cursor:

                sql = """
                          MERGE INTO state_config AS target
                          USING (SELECT 
                                   %s AS state_id, 
                                   %s AS attribute, 
                                   %s AS data) AS source
                             ON target.state_id = source.state_id 
                            AND target.attribute = source.attribute
                          WHEN MATCHED THEN 
                              UPDATE SET data = source.data
                          WHEN NOT MATCHED THEN 
                              INSERT (state_id, attribute, data)
                              VALUES (
                                   source.state_id, 
                                   source.attribute, 
                                   source.data)
                      """

                for attribute in attributes:
                    values = [
                        state_id,
                        attribute['name'],
                        attribute['data']
                    ]
                    cursor.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def insert_state_columns(self, state: State, force_update: bool = False):
        state_id = create_state_id_by_state(state)
        # existing_columns = self.fetch_state_columns(state_id=state_id)

        # the columns to create and or updates
        create_or_update_columns_definitions = {
            column_name: column_definition
            for column_name, column_definition in state.columns.items()
            if column_definition.id is None
        } if not force_update else state.columns

        if not create_or_update_columns_definitions:
            return

        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                hash_key = create_state_id_by_state(state=state)

                sql = f"""
                INSERT INTO state_column (
                    id,
                    state_id, 
                    name, 
                    data_type, 
                    required, 
                    callable, 
                    min_length, 
                    max_length, 
                    dimensions, 
                    value, 
                    source_column_name)
                VALUES (
                    COALESCE(validate_column_id(%s, %s), nextval('state_column_id_seq'::regclass)),
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id, state_id)
                    DO UPDATE SET 
                        name = EXCLUDED.name, 
                        data_type = EXCLUDED.data_type,
                        required = EXCLUDED.required, 
                        callable = EXCLUDED.callable,
                        min_length = EXCLUDED.min_length,
                        max_length = EXCLUDED.max_length,
                        value = EXCLUDED.value
                RETURNING id 
                """

                for column, column_definition in create_or_update_columns_definitions.items():
                    values = [
                        # actual values for the WITH statement in the sql above
                        column_definition.id,  # first id within the WITH statement
                        state_id,  # first state_id within the WITH statement

                        # actual values for the insert or update
                        state_id,
                        column_definition.name,
                        column_definition.data_type,
                        column_definition.required,
                        column_definition.callable,
                        column_definition.min_length,
                        column_definition.max_length,
                        column_definition.dimensions,
                        column_definition.value,
                        column_definition.source_column_name
                    ]

                    cursor.execute(sql, values)

                    # fetch the id from the returning sql statement
                    if not column_definition.id:
                        column_definition.id = cursor.fetchone()[0]

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

        return hash_key

    def insert_state_columns_data(self, state: State, incremental: bool = False):
        state_id = create_state_id_by_state(state)
        columns = self.fetch_state_columns(state_id)

        if not columns:
            logging.warning(f'no data found for state id: {state_id}, '
                            f'name: {state.config.name}')
            return

        conn = self.create_connection()
        last_persisted_position_index = 0
        try:

            track_mapping = set()
            with conn.cursor() as cursor:

                # sql = f"""insert into state_column_data (column_id, data_index, data_value) values (%s, %s, %s)"""
                sql = """
                    MERGE INTO state_column_data AS target
                    USING (SELECT %s AS column_id, %s AS data_index, %s AS data_value) AS source
                       ON target.column_id = source.column_id 
                      AND target.data_index = source.data_index
                    WHEN MATCHED THEN 
                        UPDATE SET data_value = source.data_value
                    WHEN NOT MATCHED THEN 
                        INSERT (column_id, data_index, data_value)
                        VALUES (source.column_id, source.data_index, source.data_value)
                """

                for column, header in columns.items():
                    if column not in state.data:
                        logging.warning(f'no data found for column {column}, '
                                        f'ignorable if column is a constant or function')
                        continue

                    column_id = header.id

                    if incremental:

                        data_count = state.data[column].count
                        for data_index in range(state.persisted_position, data_count):
                            column_row_data = state.data[column].values[data_index]
                            values = [
                                column_id,
                                data_index,
                                column_row_data
                            ]
                            cursor.execute(sql, values)

                            if column == 'state_key':
                                track_mapping.add(column_row_data)

                        # update the last position
                        last_persisted_position_index = data_count - 1
                    else:
                        track_mapping = None

                        for data_index, column_row_data in enumerate(state.data[column].values):
                            values = [
                                column_id,
                                data_index,
                                column_row_data
                            ]
                            cursor.execute(sql, values)

                            # if last_position_marker != 0 and data_index < last_position_marker:
                            #     raise Exception(f'critical error handling data index position, expected {last_position_marker}>={data_index}')

                            last_persisted_position_index = data_index

            conn.commit()
            state.persisted_position = last_persisted_position_index
            return track_mapping
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def fetch_state_key_definition(self, state_id: str, definition_type: str) \
            -> Optional[List[StateDataKeyDefinition]]:
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""
                    select 
                        id,
                        state_id, 
                        name, 
                        alias, 
                        required, 
                        callable,
                        definition_type
                     from state_column_key_definition 
                     where state_id = %s
                       and definition_type = %s
                """

                cursor.execute(sql, [state_id, definition_type])
                rows = cursor.fetchall()

                if not rows:
                    logging.debug(f'no key definition found for {state_id} and {definition_type}')
                    return

                key_definitions = map_rows_to_dicts(cursor, rows=rows)
                return [
                    StateDataKeyDefinition.model_validate(definition)
                    for definition in key_definitions
                ]
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def insert_state_primary_key_definition(self, state: State) \
            -> List[StateDataKeyDefinition]:
        primary_key_definition = state.config.primary_key
        return self.insert_state_key_definition(
            state=state,
            key_definition_type='primary_key',
            definitions=primary_key_definition)

    def insert_query_state_inheritance_key_definition(self, state: State) \
            -> List[StateDataKeyDefinition]:
        query_state_inheritance = state.config.query_state_inheritance
        return self.insert_state_key_definition(
            state=state,
            key_definition_type='query_state_inheritance',
            definitions=query_state_inheritance)

    def insert_remap_query_state_columns_key_definition(self, state: State) \
            -> List[StateDataKeyDefinition]:
        remap_query_state_columns = state.config.remap_query_state_columns
        return self.insert_state_key_definition(
            state=state,
            key_definition_type='remap_query_state_columns',
            definitions=remap_query_state_columns)

    def insert_template_columns_key_definition(self, state: State) \
            -> List[StateDataKeyDefinition]:
        template_columns = state.config.template_columns
        return self.insert_state_key_definition(
            state=state,
            key_definition_type='template_columns',
            definitions=template_columns)

    def insert_state_key_definition(self, state: State, key_definition_type: str,
                                    definitions: List[StateDataKeyDefinition]) \
            -> List[StateDataKeyDefinition]:

        state_id = create_state_id_by_state(state=state)

        if not definitions:
            logging.info(
                f'no key definitions defined for state_id: {state_id}, key_definition_type: {key_definition_type}')
            return

        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql_insert = """
                    INSERT INTO state_column_key_definition (
                        state_id, 
                        name, 
                        alias, 
                        required, 
                        callable, 
                        definition_type)
                    VALUES (%(state_id)s, %(name)s, %(alias)s, %(required)s, %(callable)s, %(definition_type)s)
                    RETURNING id
                """

                sql_update = """
                    UPDATE state_column_key_definition SET
                        name = %(name)s, 
                        alias = %(alias)s, 
                        required = %(required)s, 
                        callable = %(callable)s, 
                        definition_type = %(definition_type)s
                     WHERE state_id = %(state_id)s AND id = %(id)s 
                """

                # prepare to insert column key definitions
                for key_definition in definitions:

                    values = {
                        'state_id': state_id,
                        'name': key_definition.name,
                        'alias': key_definition.alias,
                        'required': key_definition.required,
                        'callable': key_definition.callable,
                        'definition_type': key_definition_type
                    }

                    sql = sql_insert
                    if key_definition.id:
                        sql = sql_update
                        values = {**values, 'id': key_definition.id}

                    cursor.execute(sql, values)

                    # fetch the id from the returning sql statement
                    if not key_definition.id:
                        key_definition.id = cursor.fetchone()[0]

                conn.commit()

            return definitions
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def fetch_state_column_data_mappings(self, state_id) \
            -> Optional[Dict[str, StateDataColumnIndex]]:
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""
                    select state_key, data_index from state_column_data_mapping where state_id = %s
                """

                cursor.execute(sql, [state_id])
                rows = cursor.fetchall()

                if not rows:
                    logging.debug(f'no mapping found for state_id: {state_id}')
                    return

                mappings: Dict[str, StateDataColumnIndex] = {}
                for row in rows:
                    state_key = row[0]
                    state_index = row[1]

                    if state_key in mappings:
                        mappings[state_key].add_index_value(state_index)
                    else:
                        mappings[state_key] = StateDataColumnIndex(
                            key=state_key,
                            values=[state_index]
                        )

            return mappings
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def insert_state_column_data_mapping(self, state: State, state_key_mapping_set: set = None):

        if not state.mapping:
            logging.warning(f'no state mapping found, cannot derive state key mapping without a '
                            f'state key from a state within the data state set')
            return

        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:

                sql = """
                           MERGE INTO state_column_data_mapping AS target
                           USING (SELECT %s AS state_id, %s AS state_key, %s AS data_index) AS source
                              ON target.state_id = source.state_id 
                             AND target.state_key = source.state_key
                             AND target.data_index = source.data_index
                           WHEN NOT MATCHED THEN 
                               INSERT (state_id, state_key, data_index)
                               VALUES (source.state_id, source.state_key, source.data_index)
                       """

                # derive the state id
                state_id = create_state_id_by_state(state)

                if state_key_mapping_set:
                    for state_key in state_key_mapping_set:
                        if state_key not in state.mapping:
                            logging.warning(
                                f'no values specified for state.mapping state key {state_key} in state_id: {state_id}')
                            continue

                        # state mapping
                        state_mapping = state.mapping[state_key]
                        for data_index in state_mapping.values:
                            values = [
                                state_id,
                                state_key,
                                data_index
                            ]
                            cursor.execute(sql, values)

                else:
                    for state_key, state_mapping in state.mapping.items():
                        if not state_mapping.values:
                            logging.warning(
                                f'no values specified for state.mapping state key {state_key} in state_id: {state_id}')
                            continue

                        for data_index in state_mapping.values:
                            values = [
                                state_id,
                                state_key,
                                data_index
                            ]
                            cursor.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def load_state_basic(self, state_id: str) -> Optional[State]:
        state = self.fetch_state(state_id=state_id)
        if not state:
            return None

        state_type = state.state_type

        # rebuild the key definitions
        primary_key = self.fetch_state_key_definition(
            state_id=state_id,
            definition_type="primary_key")

        query_state_inheritance = self.fetch_state_key_definition(
            state_id=state_id,
            definition_type="query_state_inheritance")

        remap_query_state_columns = self.fetch_state_key_definition(
            state_id=state_id,
            definition_type="remap_query_state_columns")

        template_columns = self.fetch_state_key_definition(
            state_id=state_id,
            definition_type="template_columns")

        # fetch list of attributes associated to this state, if any
        config_attributes = self.fetch_state_config(state_id=state_id)
        general_attributes = {
            "primary_key": primary_key,
            "query_state_inheritance": query_state_inheritance,
            "remap_query_state_columns": remap_query_state_columns,
            "template_columns": template_columns,
        }

        if 'StateConfig' == state_type:
            config = StateConfig(
                **general_attributes,
                **config_attributes
            )
        elif 'StateConfigLM' == state_type:
            config = StateConfigLM(
                **general_attributes,
                **config_attributes
            )
        elif 'StateConfigVisual' == state_type:
            config = StateConfigVisual(
                **general_attributes,
                **config_attributes
            )
        elif 'StateConfigCode' == state_type:
            config = StateConfigCode(
                **general_attributes,
                **config_attributes
            )
        else:
            raise NotImplementedError(f'unsupported type {state_type}')

        state.config = config
        state.persisted_position = state.count - 1

        # count = state.count
        # build the state definition
        # state_instance = State(
        #     **state_dict,
        #     config=config,
        #     persisted_position=count - 1,
        # )

        return state

    def load_state_columns(self, state_id: str) \
            -> Optional[Dict[str, StateDataColumnDefinition]]:

        # rebuild the column definition
        return self.fetch_state_columns(state_id=state_id)

    def load_state_data(self, columns: Dict[str, StateDataColumnDefinition]) \
            -> Optional[Dict[str, StateDataRowColumnData]]:

        # rebuild the data values by column and values
        return {
            column: self.fetch_state_data_by_column_id(column_definition.id)
            for column, column_definition in columns.items()
            # if not column_definition.value  # TODO REMOVE since we now store all constant and expression values in .data[col].values[]  ...old: only return row data that is not a function or a constant
        }

    def load_state_data_mappings(self, state_id: str) \
            -> Optional[Dict[str, StateDataColumnIndex]]:

        # rebuild the data state mapping
        return self.fetch_state_column_data_mappings(
            state_id=state_id)

    def load_state(self, state_id: str, load_data: bool = True) -> Optional[State]:
        # basic state instance
        state = self.load_state_basic(state_id=state_id)

        if not state:
            return None

        # load additional details about the state
        state.columns = self.load_state_columns(state_id=state_id)
        state.data = self.load_state_data(columns=state.columns)
        state.mapping = self.load_state_data_mappings(state_id=state_id)

        return state

    def delete_state_cascade(self, state_id):
        self.delete_state_data(state_id=state_id)
        self.delete_state_column(state_id=state_id)
        self.delete_state_config_key_definitions(state_id=state_id)
        self.delete_state_config(state_id=state_id)
        self.delete_state(state_id=state_id)

    def delete_state(self, state_id):

        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = "DELETE FROM state WHERE id = %s"
                cursor.execute(sql, [state_id])
            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def delete_state_config(self, state_id):

        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = "DELETE FROM state_config WHERE state_id = %s"
                cursor.execute(sql, [state_id])
            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def reset_state_column_data_zero(self, state_id, zero: int = 0) -> int:
        return self.execute_update(
            table="state",
            update_values={
                'count': zero
            },
            conditions={
                'id': state_id
            },
        )

    def delete_state_column_data_mapping(self, state_id, column_id: int = None) -> int:
        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = "DELETE FROM state_column_data_mapping WHERE state_id = %s"
                cursor.execute(sql, [state_id])
            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def delete_state_column(self, state_id: str, column_id: int = None) -> int:
        if not state_id:
            raise ValueError(f'state id must be specified')

        return self.execute_delete_query(
            sql="DELETE FROM state_column",
                conditions=[{
                    "id": column_id,
                    "state_id": state_id
                }])

    def delete_state_column_data(self, state_id, column_id: int = None) -> int:

        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = "DELETE FROM state_column_data WHERE column_id in (SELECT id FROM state_column WHERE state_id = %s)"
                cursor.execute(sql, [state_id])
            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)


    def delete_state_data(self, state_id: str):
        self.delete_state_column_data_mapping(state_id=state_id)
        self.delete_state_column_data(state_id=state_id)
        self.reset_state_column_data_zero(state_id=state_id)

    def delete_state_config_key_definition(self, state_id: str, definition_type: str, definition_id: int) -> int:
        if not (state_id or definition_type or definition_id):
            raise PermissionError(
                f'state_id, definition_type and definition_id must be specified when deleting a state config key definition')

        return self.execute_delete_query(
            sql="DELETE FROM state_column_key_definition",
            conditions={
                "state_id": state_id,
                "definition_type": definition_type,
                "id": definition_id
            }
        )

    def delete_state_config_key_definitions(self, state_id):

        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = "DELETE FROM state_column_key_definition WHERE state_id = %s"
                cursor.execute(sql, [state_id])
            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def update_state_count(self, state: State) -> State:
        self.execute_update(
            table="state",
            update_values={"count": state.count},
            conditions={"id": state.id}
        )
        return state

    def save_state(self, state: State, options: dict = None) -> State:

        def fetch_option(name: str, default: Any = None):
            if not options:
                return default

            return options[name] if name in options else default

        force_update_column = fetch_option('force_update_column', False)
        first_time = state.persisted_position <= 0
        if not self.incremental or first_time:
            state = self.insert_state(state=state)
            self.insert_state_config(state=state)
            self.insert_state_columns(state=state, force_update=force_update_column)
            self.insert_state_columns_data(state=state, incremental=False)
            self.insert_state_column_data_mapping(state=state)
            self.insert_state_primary_key_definition(state=state)
            self.insert_query_state_inheritance_key_definition(state=state)
            self.insert_remap_query_state_columns_key_definition(state=state)
            self.insert_template_columns_key_definition(state=state)
        else:

            state_id = create_state_id_by_state(state)

            # the incremental function returns the list of state keys that need to be applied
            primary_key_mapping_update_set = self.insert_state_columns_data(state=state, incremental=True)

            # insert any new primary key references, provided that it was merged by the previous call
            self.insert_state_column_data_mapping(state=state, state_key_mapping_set=primary_key_mapping_update_set)

            # only save the state if there were changes made, track by primary key updates from previous calls
            if primary_key_mapping_update_set:
                self.insert_state(state=state)

        return state


class ProcessorStateDatabaseStorage(ProcessorStateRouteStorage, BaseDatabaseAccess):

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
                        maximum_index
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (processor_id, state_id, direction)
                    DO UPDATE SET 
                        count = EXCLUDED.count, 
                        status = EXCLUDED.status,
                        current_index = EXCLUDED.current_index, 
                        maximum_index = EXCLUDED.maximum_index
                    RETURNING internal_id 
                """

                # generate a new processor id based on the direction of the edge
                # if not processor_state.id:
                #     if processor_state.direction.INPUT:
                #         processor_state.id = f'{processor_state.state_id}:{processor_state.processor_id}'
                #     elif processor_state.direction.OUTPUT:
                #         processor_state.id = f'{processor_state.processor_id}:{processor_state.state_id}'

                cursor.execute(sql, [
                    processor_state.id,
                    processor_state.processor_id,
                    processor_state.state_id,
                    processor_state.direction.value,
                    processor_state.status.value,
                    processor_state.count,
                    processor_state.current_index,
                    processor_state.maximum_index
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


class MonitorLogEventDatabaseStorage(MonitorLogEventStorage, BaseDatabaseAccess):

    def fetch_monitor_log_events(
            self,
            internal_reference_id: int = None,
            user_id: str = None,
            project_id: str = None) -> Optional[List[MonitorLogEvent]]:

        if not internal_reference_id and not user_id and not project_id:
            raise ValueError(f'at least one search criteria must be defined, '
                             f'internal_reference_id, user_id or project_id')

        return self.execute_query_many(
            sql="select * from monitor_log_event",
            conditions={
                'internal_reference_id': internal_reference_id,
                'user_id': user_id,
                'project_id': project_id
            },
            mapper=lambda row: MonitorLogEvent(**row)
        )

    def delete_monitor_log_event(
            self,
            log_id: str = None,
            user_id: str = None,
            project_id: str = None,
            force: bool = False) -> int:

        # at-least one parameter must be defined (or forced)
        if not (id or user_id or project_id) and not force:
            return 0

        # delete the monitor log based on input parameters
        return self.execute_delete_query(
            "delete from monitor_log_event",
            conditions={
                "log_id": log_id,
                "user_id": user_id,
                "project_id": project_id
            }
        )



    def insert_monitor_log_event(self, monitor_log_event: MonitorLogEvent) -> MonitorLogEvent:

        try:
            conn = self.create_connection()
            with (conn.cursor() as cursor):
                sql = """
                    INSERT INTO monitor_log_event (
                        log_type,
                        internal_reference_id,
                        user_id,
                        project_id,
                        exception,
                        data
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING log_id, log_time 
                """

                cursor.execute(sql, [
                    monitor_log_event.log_type,
                    monitor_log_event.internal_reference_id,
                    monitor_log_event.user_id,
                    monitor_log_event.project_id,
                    monitor_log_event.exception,
                    monitor_log_event.data
                ])

                # fetch the id from the returning sql statement
                returned = cursor.fetchone()
                monitor_log_event.log_id = returned[0]  # serial id / sequence
                monitor_log_event.log_time = returned[1]  # log time

            conn.commit()
            return monitor_log_event
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)


class PostgresDatabaseStorage(StateMachineStorage):

    def __init__(self, database_url: str, incremental: bool = True, *args, **kwargs):
        super().__init__(
            state_storage=StateDatabaseStorage(database_url=database_url, incremental=incremental),
            processor_storage=ProcessorDatabaseStorage(database_url=database_url, incremental=incremental),
            processor_state_storage=ProcessorStateDatabaseStorage(database_url=database_url, incremental=incremental),
            processor_provider_storage=ProcessorProviderDatabaseStorage(database_url=database_url,
                                                                        incremental=incremental),
            workflow_storage=WorkflowDatabaseStorage(database_url=database_url, incremental=incremental),
            template_storage=TemplateDatabaseStorage(database_url=database_url, incremental=incremental),
            user_profile_storage=UserProfileDatabaseStorage(database_url=database_url, incremental=incremental),
            user_project_storage=UserProjectDatabaseStorage(database_url=database_url, incremental=incremental),
            monitor_log_event_storage=MonitorLogEventDatabaseStorage(database_url, incremental=incremental)
        )
