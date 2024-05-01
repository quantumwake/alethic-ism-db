import uuid

from psycopg2 import pool
from typing import List, Any, Union, Dict, Optional, Type, Callable
import logging as log

# import state and other models
from core.base_model import (
    ProcessorStateDirection,
    UserProject,
    UserProfile,
    WorkflowNode,
    WorkflowEdge
)

from core.processor_state import (
    State,
    StateDataKeyDefinition,
    StateConfigLM,
    StateConfig,
    StateDataColumnDefinition,
    StateDataRowColumnData,
    StateDataColumnIndex,
    InstructionTemplate
)

# import interfaces relevant to the storage subsystem
from core.processor_state_storage import (
    ProcessorStateStorage,
    Processor,
    ProcessorState,
    ProcessorProvider,
    StateMachineStorage,
    ProcessorStorage,
    StateStorage,
    ProviderStorage,
    TemplateStorage,
    WorkflowStorage,
    UserProjectStorage,
    UserProfileStorage
)


from .misc_utils import create_state_id_by_config, create_state_id_by_state, map_row_to_dict, map_rows_to_dicts

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
        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = """DELETE FROM workflow_node WHERE node_id = %s"""
                cursor.execute(sql, [node_id])
            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def fetch_workflow_nodes(self, project_id: str) -> Optional[List[WorkflowNode]]:
        return self.execute_query_many(
            "select * from workflow_node",
            conditions={
                "project_id": project_id
            },
            mapper=lambda row: WorkflowNode(**row)
        )

    def insert_workflow_node(self, node: WorkflowNode):
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
        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = """DELETE FROM workflow_edge WHERE source_node_id = %s and target_node_id = %s"""
                cursor.execute(sql, [source_node_id, target_node_id])
            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

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

    def insert_workflow_edge(self, edge: WorkflowEdge):
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:

                sql = """
                           INSERT INTO workflow_edge (source_node_id, target_node_id, source_handle, target_handle, animated, edge_label)
                           VALUES (%s, %s, %s, %s, %s, %s)
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
                    edge.edge_label
                ]
                cursor.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

        return edge


class ProviderDatabaseStorage(ProviderStorage, BaseDatabaseAccess):

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
        return self.execute_query_many(
            sql="SELECT * FROM processor",
            conditions={
                'project_id': project_id,
                'provider_id': provider_id
            },
            mapper=lambda row: Processor(**row))

    def fetch_processor(self, processor_id: str) -> Optional[Processor]:
        return self.execute_query_one(
            sql="SELECT * FROM processor",
            conditions={
                'id': processor_id
            },
            mapper=lambda row: Processor(**row))

    def insert_processor(self, processor: Processor) -> Processor:

        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = f"""
                    INSERT INTO processor (id, provider_id, project_id, status)
                         VALUES (%s, %s, %s, %s)
                             ON CONFLICT (id) 
                      DO UPDATE SET 
                           status = EXCLUDED.status
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
                    INSERT INTO state (id, project_id, state_type, count) 
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) 
                    DO UPDATE SET 
                        state_type = EXCLUDED.state_type,
                        count = EXCLUDED.count
                """

                # setup data values for state
                values = [
                    state.id,
                    state.project_id,
                    state.state_type,
                    state.count
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
                "name": "storage_class",
                "data": "database"
            },
            {
                "name": "name",
                "data": state.config.name
            }
        ]

        # if the config is LM then we have additional information
        if isinstance(state.config, StateConfigLM):
            config = state.config
            #
            # def convert_template(template_path: str, template_type: str):
            #     if template_path:
            #         template = general_utils.load_template(template_config_file=template_path)
            #         template_path = template['name']  # change the path to only the name for db storage
            #         template_id = self.insert_template(
            #             template_path=template_path,
            #             template_content=template['template_content'],
            #             template_type=template_type)
            #         return template_id
            #     else:
            #         return None

            # if we are loading the template into the database for the first time
            # usually when the storage class is default set to a file instead
            # if 'storage_class' not in config.__dict__ or 'file' == config.storage_class.lower():
            #     config.storage_class = 'database'
            #     user_template_id = convert_template(config.user_template_path, "user_template")
            #     user_template_path = convert_template(config.user_template_path, "user_template")
                # system_template_id = convert_template(config.system_template_path, "system_template")
                # system_template_path = convert_template(config.system_template_path, "system_template")
            # else:

            # additional parameters required for config lm
            attributes.extend([
                # {
                #     "name": "provider_name",
                #     "data": config.provider_name
                # },
                # {
                #     "name": "model_name",
                #     "data": config.model_name
                # },
                {
                    "name": "user_template_id",
                    "data": config.user_template_id
                },
                {
                    "name": "system_template_id",
                    "data": config.system_template_id
                }
            ])

        # create a new state
        state_id = create_state_id_by_state(state=state)

        if not attributes:
            logging.info(f'no additional attributes specified for '
                         f'state_id: {state_id}, name: {state.config.name}, '
                         f'version: {state.config.version}')
            return

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

    def insert_state_columns(self, state: State):
        state_id = create_state_id_by_state(state)
        existing_columns = self.fetch_state_columns(state_id=state_id)

        create_columns = {column: header
                          for column, header in state.columns.items()
                          if column not in existing_columns}

        if not create_columns:
            return

        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                hash_key = create_state_id_by_state(state=state)

                sql = f"""
                insert into state_column (
                    state_id, name, data_type, "null", 
                    min_length, max_length, dimensions, value, 
                    source_column_name)
                values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                for column, column_definition in create_columns.items():
                    values = [
                        state_id,
                        column_definition.name,
                        column_definition.data_type,
                        column_definition.null,
                        column_definition.min_length,
                        column_definition.max_length,
                        column_definition.dimensions,
                        column_definition.value,
                        column_definition.source_column_name
                    ]

                    cursor.execute(sql, values)

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
                    INSERT INTO state_column_key_definition (state_id, name, alias, required, callable, definition_type)
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
            if not column_definition.value  # only return row data that is not a function or a constant
        }

    def load_state_data_mappings(self, state_id: str) \
            -> Optional[Dict[str, StateDataColumnIndex]]:

        # rebuild the data state mapping
        return self.fetch_state_column_data_mappings(
            state_id=state_id)

    def load_state(self, state_id: str, load_data: bool = True):
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
        self.delete_state_column_data_mapping(state_id=state_id)
        self.delete_state_column_data(state_id=state_id)
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

    def delete_state_column_data_mapping(self, state_id):

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

    def delete_state_column(self, state_id):

        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = "DELETE FROM state_column WHERE state_id = %s"
                cursor.execute(sql, [state_id])
            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def delete_state_column_data(self, state_id):

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

    def save_state(self, state: State) -> State:

        first_time = state.persisted_position <= 0

        # TODO needs revision as columns and structures may change, need a way to check for
        #  consistency similar to how it is done at the processor apply_column,apply_data functions
        if not self.incremental or first_time:
            state = self.insert_state(state=state)
            self.insert_state_config(state=state)
            self.insert_state_columns(state=state)
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


class ProcessorStateDatabaseStorage(ProcessorStateStorage, BaseDatabaseAccess):

    def fetch_prcoessor_state_details(self, processor_id, state_id, direction: ProcessorStateDirection, provider_id):
        return self.execute_query_many(
            sql="""select ps.processor_id,
                       ps.state_id,
                       ps.direction,
                       p.project_id,
                       p.provider_id
                  from processor_state ps
                 inner join processor p
                    on p.id = ps.processor_id""",
            conditions={
                'processor_id': processor_id,
                'state_id': state_id,
                'direction': direction.value if direction else None
            },
            mapper=lambda row: ProcessorState(**row))

    def fetch_processor_state(self, processor_id: str = None, state_id: str = None, direction: ProcessorStateDirection = None) \
            -> Optional[List[ProcessorState]]:

        return self.execute_query_many(
            sql="SELECT * FROM processor_state",
            conditions={
                'processor_id': processor_id,
                'state_id': state_id,
                'direction': direction.value if direction else None
            },
            mapper=lambda row: ProcessorState(**row))

    def insert_processor_state(self, processor_state: ProcessorState) \
            -> ProcessorState:

        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO processor_state (
                        processor_id,
                        state_id,
                        direction
                    )
                    VALUES (%s, %s, %s)
                    ON CONFLICT (processor_id, state_id, direction)
                    DO NOTHING
                """

                cursor.execute(sql, [
                    processor_state.processor_id,
                    processor_state.state_id,
                    processor_state.direction.value
                ])

            conn.commit()
            return processor_state
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)


class PostgresDatabaseStorage(StateMachineStorage,
                              StateDatabaseStorage,
                              ProcessorDatabaseStorage,
                              ProcessorStateDatabaseStorage,
                              ProviderDatabaseStorage,
                              WorkflowDatabaseStorage,
                              TemplateDatabaseStorage,
                              UserProfileDatabaseStorage,
                              UserProjectDatabaseStorage):

    # def __init__(self, database_url: str, incremental: bool = True):
        # super().__init__(
        #     database_url=database_url,
        #     incremental=incremental
        # )

    pass