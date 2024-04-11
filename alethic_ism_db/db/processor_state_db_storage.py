# The Alethic Instruction-Based State Machine (ISM) is a versatile framework designed to 
# efficiently process a broad spectrum of instructions. Initially conceived to prioritize
# animal welfare, it employs language-based instructions in a graph of interconnected
# processing and state transitions, to rigorously evaluate and benchmark AI models
# apropos of their implications for animal well-being. 
# 
# This foundation in ethical evaluation sets the stage for the framework's broader applications,
# including legal, medical, multi-dialogue conversational systems.
# 
# Copyright (C) 2023 Kasra Rasaee, Sankalpa Ghose, Yip Fai Tse (Alethic Research) 
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# 
#
import uuid

from psycopg2 import pool
from typing import List, Any, Union, Dict
import logging as log

from core.processor_state import (
    State,
    StateDataKeyDefinition,
    StateConfigLM,
    StateConfig,
    StateDataColumnDefinition,
    StateDataRowColumnData,
    StateDataColumnIndex, InstructionTemplate, ProcessorStatus, implicit_count_with_force_count
)
from core.processor_state_storage import (
    ProcessorStateStorage,
    Processor,
    ProcessorState
)
from core.utils import general_utils
from core.utils.state_utils import validate_processor_status_change

from .misc_utils import create_state_id_by_config
from .models import UserProject, UserProfile, WorkflowNode, WorkflowEdge

logging = log.getLogger(__name__)


class BaseDatabaseAccess():

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

    def map_row_to_dict(self, cursor, row):
        """ Maps a single row to a dictionary using column names from the cursor. """
        columns = [col[0] for col in cursor.description]
        return dict(zip(columns, row))

    def map_rows_to_dicts(self, cursor, rows):
        """ Maps a list of rows to a list of dictionaries using column names from the cursor. """
        return [self.map_row_to_dict(cursor, row) for row in rows]

    def create_connection(self):
        return self.connection_pool.getconn()

    def release_connection(self, conn):
        self.connection_pool.putconn(conn)

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

    def fetch_user_project(self, project_id: str):
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""
                    select * from user_project where project_id = %s
                """

                cursor.execute(sql, [project_id])
                row = cursor.fetchone()
                if row is None:
                    return None

                row_dict = self.map_row_to_dict(cursor=cursor, row=row)
                data = UserProject(**row_dict)

            return data
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

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

        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""
                select * from user_project where user_id = %s
                """

                cursor.execute(sql, [user_id])
                rows = cursor.fetchall()
                results = self.map_rows_to_dicts(cursor, rows) if rows else None
                # result = [State(**r) for r in results]

            return [UserProject(**s) for s in results]
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

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

    def fetch_workflow_nodes(self, project_id: str) -> Union[List[WorkflowNode], None]:

        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""
                select * from workflow_node where project_id = %s
                """

                cursor.execute(sql, [project_id])
                rows = cursor.fetchall()
                if not rows:
                    return None

                results = self.map_rows_to_dicts(cursor, rows) if rows else None

            return [WorkflowNode(**node) for node in results]
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

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

    def fetch_workflow_edges(self, project_id: str) -> Union[List[WorkflowEdge], None]:

        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""
                    select * from workflow_edge 
                     where source_node_id in (select node_id 
                                                from workflow_node 
                                               where project_id = %s) 
                        or target_node_id in (select node_id
                                                from workflow_node
                                               where project_id = %s)
                """

                cursor.execute(sql, [project_id, project_id])
                rows = cursor.fetchall()
                if not rows:
                    return None

                results = self.map_rows_to_dicts(cursor, rows) if rows else None

            return [WorkflowEdge(**edge) for edge in results]
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

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


class ProcessorStateDatabaseStorage(ProcessorStateStorage, BaseDatabaseAccess):

    # TODO add async support
    # async def create_connection_async(self):
    #     """Create a connection to the PostgreSQL database."""
    #
    #     connection = await connect(
    #         "dbname=my_database user=postgres password=password"
    #     )
    #     return connection

    def create_state_id_by_state(self, state: State):
        if not state.id:
            return create_state_id_by_config(config=state.config)
        else:
            return state.id

    def fetch_templates(self, project_id: str = None):
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:

                sql = f"""
                    select 
                        template_id, 
                        template_path, 
                        template_content, 
                        template_type, 
                        project_id 
                      from template
                """

                if project_id:
                    sql = f"{sql} where project_id = %s"  # fetch project level templates
                    cursor.execute(sql, [project_id])
                else:
                    sql = f"{sql} where project_id is null"  # only fetch global templates
                    cursor.execute(sql, [])

                # fetch all data
                rows = cursor.fetchall()
                data = [InstructionTemplate(
                    template_id=row[0],
                    template_path=row[1],
                    template_content=row[2],
                    template_type=row[3],
                    project_id=row[4]
                ) for row in rows]

            return data
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def fetch_procesors_by_project(self, project_id: str) -> List[Processor]:
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""
                           select * from processor where project_id = %s
                       """

                cursor.execute(sql, [project_id])
                rows = cursor.fetchall()
                results = self.map_rows_to_dicts(cursor=cursor, rows=rows)

            return [Processor(**p) for p in results]

        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def fetch_processor(self, processor_id) -> Processor:
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""
                    select * from processor where id = %s
                """

                cursor.execute(sql, [processor_id])
                row = cursor.fetchone()
                result = self.map_row_to_dict(cursor=cursor, row=row)

            return Processor(**result)
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def fetch_template(self, template_id: str):
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""
                    select template_id, template_path, template_content, template_type, project_id from template
                    where template_id = %s
                """

                cursor.execute(sql, [template_id])
                row = cursor.fetchone()
                data = InstructionTemplate(
                    template_id=row[0],
                    template_path=row[1],
                    template_content=row[2],
                    template_type=row[3],
                    project_id=row[4] if row[4] else None
                )

            return data
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def fetch_state_data_by_column_id(self, column_id: int):
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

    def fetch_state_columns(self, state_id: str) -> List[StateDataColumnDefinition]:
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""select * from state_column where state_id = %s"""
                cursor.execute(sql, [state_id])
                rows = cursor.fetchall()
                results = self.map_rows_to_dicts(cursor, rows)
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

    def fetch_states_by_project(self, project_id: str) -> List[State]:

        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""
                select * from state where project_id = %s
                """

                cursor.execute(sql, [project_id])
                rows = cursor.fetchall()
                results = self.map_rows_to_dicts(cursor, rows) if rows else None
                # result = [State(**r) for r in results]

            return [State(**s) for s in results]
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def fetch_states(self):

        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""
                select * from state
                """

                cursor.execute(sql, [])
                rows = cursor.fetchall()
                results = self.map_rows_to_dicts(cursor, rows) if rows else None
                # result = [State(**r) for r in results]

            return results
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def fetch_state_by_state_id(self, state_id: str):
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""select * from state where id = %s"""
                cursor.execute(sql, [state_id])
                row = cursor.fetchone()
                result = self.map_row_to_dict(cursor, row) if row else None
            return result
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def fetch_state_by_name_version(self, name: str, version: str, state_type: str):

        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""
                select * from state 
                 where lower(name) = lower(%s) 
                   and lower(version) = lower(%s) 
                   and lower(state_type) = lower(%s)
                """

                # # set the version to blank if not available
                # if not version:
                #     version = "Version 0.0"

                values = [
                    name.strip(),
                    version.strip(),
                    state_type.strip()
                ]

                cursor.execute(sql, values)
                rows = cursor.fetchall()
                results = self.map_rows_to_dicts(cursor, rows) if rows else None

            return results
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    #
    # async def insert_state_async(self, state: State):
    #     conn = await self.create_connection_async()
    #     await self._insert_state(conn, state=state)

    # TODO probably should be using async support, with sqlalchemy instead of doing it this way
    #  maybe do this in the future when we get some more time.
    #
    # def insert_model(self, model: Model):
    #     conn = self.create_connection()
    #
    #     try:
    #         with conn.cursor() as cursor:
    #
    #             sql = f"""
    #                 INSERT INTO model (provider_name, model_name)
    #                      VALUES (%s, %s)
    #                          ON CONFLICT (provider_name, model_name)
    #                   DO UPDATE SET provider_name = EXCLUDED.provider_name, model_name = EXCLUDED.model_name
    #                 RETURNING id
    #             """
    #
    #             # sql = f"""insert into model (provider_name, model_name) values (%s, %s) RETURNING id"""
    #             values = [model.provider_name, model.model_name]
    #             cursor.execute(sql, values)
    #
    #             # fetch id value
    #             model.id = cursor.fetchone()[0]
    #
    #         conn.commit()
    #     except Exception as e:
    #         logging.error(e)
    #         raise e
    #     finally:
    #         self.release_connection(conn)
    #
    #     return model

    def insert_state(self, state: State):
        conn = self.create_connection()

        # get the configuration type for this state
        state_id = self.create_state_id_by_state(state=state)

        try:
            with conn.cursor() as cursor:

                sql = """
                    INSERT INTO state (id, name, state_type, count, version) 
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) 
                    DO UPDATE SET count = EXCLUDED.count
                """

                # setup data values for state
                values = [
                    state_id,
                    state.config.name.strip(),
                    state.state_type,
                    state.count,
                    state.config.version.strip() if state.config.version else state.config.version
                ]

                cursor.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

        return state_id

    def fetch_state_config(self, state_id: str):

        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""
                select * from state_config where state_id = %s 
                """
                cursor.execute(sql, [state_id])
                rows = cursor.fetchall()
                results = self.map_rows_to_dicts(cursor, rows) if rows else {}

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

    def fetch_processors(self):
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""select * from processor"""

                cursor.execute(sql, [])
                rows = cursor.fetchall()
                results = self.map_rows_to_dicts(cursor, rows) if rows else None
                results = [Processor(**row) for row in results]

            return results
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def fetch_processor_states(self):
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""select * from processor_state"""

                cursor.execute(sql, [])
                rows = cursor.fetchall()
                results = self.map_rows_to_dicts(cursor, rows) if rows else None
                results = [ProcessorState(**row) for row in results]

            return results
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

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

    def insert_template(self,
                        template_id: str = None,
                        template_path: str = None,
                        template_content: str = None,
                        template_type: str = None,
                        project_id: str = None,
                        instruction_template: InstructionTemplate = None):

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

                if instruction_template:
                    template_id = instruction_template.template_id
                    template_path = instruction_template.template_path
                    template_content = instruction_template.template_content
                    template_type = instruction_template.template_type
                    project_id = instruction_template.project_id

                elif not (template_id or template_path or template_content or template_type):
                    raise ValueError(f'must specify either the instruction_template or template_path, '
                                     f'template_content and template_type')

                # create a template id if it is not specified
                template_id = template_id if template_id else str(uuid.uuid4())

                values = [
                    template_id,
                    template_path,
                    template_content,
                    template_type,
                    project_id
                ]
                cursor.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

        return template_id

    def fetch_processor_states_by(self, processor_id: str,
                                  input_state_id: str = None,
                                  output_state_id: str = None) -> Union[List[ProcessorState], ProcessorState]:
        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:

                values = [processor_id]

                sql = """
                    select 
                        processor_id, 
                        input_state_id,
                        output_state_id,
                        status
                    from processor_state
                   where processor_id = %s
                """

                if input_state_id:
                    values.append(input_state_id)
                    sql = f"""{sql}
                    and input_state_id = %s
                    """

                if output_state_id:
                    values.append(output_state_id)
                    sql = f"""{sql}
                    and output_state_id = %s
                    """

                cursor.execute(sql, values)
                rows = cursor.fetchall()

                results = self.map_rows_to_dicts(cursor=cursor, rows=rows)
                results = [ProcessorState(**row) for row in results]

            if len(results) == 1:
                return results[0]
            else:
                return results

        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def update_processor_state(self, processor_state: ProcessorState):

        if not (processor_state.processor_id and
                processor_state.input_state_id and
                processor_state.output_state_id and
                processor_state.status):
            raise ValueError(f'processor id, input state id, output state id and status must be set')

        current_state = self.fetch_processor_states_by(
            processor_id=processor_state.processor_id,
            input_state_id=processor_state.input_state_id,
            output_state_id=processor_state.output_state_id)

        #
        persist = True
        new_status = processor_state.status

        # if the current status is not set <AND> the new status is not created, raise now allowed exception
        if not current_state:
            current_status = None
            if new_status not in [ProcessorStatus.CREATED]:
                raise AssertionError(
                    f'invalid first processor status, must be set to CREATED status for initial processor state')
        else:
            current_status = current_state.status

        # validate the current status change
        validate_processor_status_change(
            current_status=current_status,
            new_status=processor_state.status)

        # update the current status in the processor state
        self._change_processor_state(processor_state=processor_state)

    def _change_processor_state(self, processor_state: ProcessorState):

        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = """
                INSERT INTO processor_state (
                    processor_id, 
                    input_state_id,
                    output_state_id,
                    status)
                VALUES (%s, %s, %s, %s) 
                ON CONFLICT (processor_id, input_state_id, output_state_id) 
                DO UPDATE SET status = EXCLUDED.status
                """

                cursor.execute(sql, [
                    processor_state.processor_id,
                    processor_state.input_state_id,
                    processor_state.output_state_id,
                    processor_state.status.value
                ])

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def insert_processor(self, processor: Processor):

        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = f"""
                    INSERT INTO processor (id, type)
                         VALUES (%s, %s)
                             ON CONFLICT (id, type) 
                      DO UPDATE SET 
                           id = EXCLUDED.id, 
                           type = EXCLUDED.type
                """
                cursor.execute(sql, [
                    processor.id,
                    processor.type
                ])

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

        return processor

    def insert_state_config(self, state: State):

        # switch it to a database storage class
        attributes = [
            {
                "name": "storage_class",
                "data": "database"
            }
        ]

        # if the config is LM then we have additional information
        if isinstance(state.config, StateConfigLM):
            config = state.config

            def convert_template(template_path: str, template_type: str):
                if template_path:
                    template = general_utils.load_template(template_config_file=template_path)
                    template_path = template['name']  # change the path to only the name for db storage
                    template_id = self.insert_template(
                        template_path=template_path,
                        template_content=template['template_content'],
                        template_type=template_type)
                    return template_id
                else:
                    return None

            # if we are loading the template into the database for the first time
            # usually when the storage class is default set to a file instead
            if 'storage_class' not in config.__dict__ or 'file' == config.storage_class.lower():
                config.storage_class = 'database'
                user_template_id = convert_template(config.user_template_path, "user_template")
                # user_template_path = convert_template(config.user_template_path, "user_template")
                system_template_id = convert_template(config.system_template_path, "system_template")
                # system_template_path = convert_template(config.system_template_path, "system_template")
            else:
                # user_template_path = config.user_template_path
                user_template_id = config.user_template_id
                # system_template_path = config.system_template_path
                system_template_id = config.system_template_id

            # additional parameters required for config lm
            attributes.extend([
                {
                    "name": "provider_name",
                    "data": config.provider_name
                },
                {
                    "name": "model_name",
                    "data": config.model_name
                },
                {
                    "name": "user_template_id",
                    "data": user_template_id
                },
                {
                    "name": "system_template_id",
                    "data": system_template_id
                }
            ])

        # create a new state
        state_id = self.create_state_id_by_state(state=state)

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
        state_id = self.create_state_id_by_state(state)
        existing_columns = self.fetch_state_columns(state_id=state_id)

        create_columns = {column: header
                          for column, header in state.columns.items()
                          if column not in existing_columns}

        if not create_columns:
            return

        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                hash_key = self.create_state_id_by_state(state=state)

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
        state_id = self.create_state_id_by_state(state)
        columns = self.fetch_state_columns(state_id)

        if not columns:
            logging.warning(f'no data found for state id: {state_id}, '
                            f'name: {state.config.name}, '
                            f'version: {state.config.version}')
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

    def fetch_state_key_definition(self, state_id: str, definition_type: str):
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""
                    select 
                        state_id, 
                        name, 
                        alias, 
                        required, 
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

                key_definitions = self.map_rows_to_dicts(cursor, rows=rows)
                return [
                    StateDataKeyDefinition.model_validate(definition)
                    for definition in key_definitions
                ]
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def insert_state_primary_key_definition(self, state: State):
        primary_key_definition = state.config.primary_key
        self.insert_state_key_definition(state=state,
                                         key_definition_type='primary_key',
                                         definitions=primary_key_definition)

    def insert_query_state_inheritance_key_definition(self, state: State):
        query_state_inheritance = state.config.query_state_inheritance
        self.insert_state_key_definition(state=state,
                                         key_definition_type='query_state_inheritance',
                                         definitions=query_state_inheritance)

    def insert_remap_query_state_columns_key_definition(self, state: State):
        remap_query_state_columns = state.config.remap_query_state_columns
        self.insert_state_key_definition(state=state,
                                         key_definition_type='remap_query_state_columns',
                                         definitions=remap_query_state_columns)

    def insert_template_columns_key_definition(self, state: State):
        template_columns = state.config.template_columns
        self.insert_state_key_definition(state=state,
                                         key_definition_type='template_columns',
                                         definitions=template_columns)

    def insert_state_key_definition(self,
                                    state: State,
                                    key_definition_type: str,
                                    definitions: List[StateDataKeyDefinition]):

        state_id = self.create_state_id_by_state(state=state)

        if not definitions:
            logging.info(
                f'no key definitions defined for state_id: {state_id}, key_definition_type: {key_definition_type}')
            return

        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:

                sql = """
                           MERGE INTO state_column_key_definition AS target
                           USING (SELECT 
                                    %s AS state_id, 
                                    %s AS name, 
                                    %s AS alias, 
                                    %s AS required, 
                                    %s AS definition_type) AS source
                              ON target.state_id = source.state_id 
                             AND target.name = source.name
                             AND target.definition_type = source.definition_type
                           WHEN NOT MATCHED THEN 
                               INSERT (state_id, name, alias, required, definition_type)
                               VALUES (
                                    source.state_id, 
                                    source.name, 
                                    source.alias, 
                                    source.required, 
                                    source.definition_type)
                       """

                # prepare to insert column key definitions
                for key_definition in definitions:
                    values = [
                        state_id,
                        key_definition.name,
                        key_definition.alias,
                        key_definition.required,
                        key_definition_type,
                    ]
                    cursor.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def fetch_state_column_data_mappings(self, state_id):
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

                mappings = {}
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
                state_id = self.create_state_id_by_state(state)

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

    def load_state_basic(self, state_id: str):
        state_dict = self.fetch_state_by_state_id(state_id=state_id)
        if not state_dict:
            return None

        state_type = state_dict['state_type']

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
            "name": state_dict['name'],
            "version": state_dict['version'],
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

        count = state_dict['count']
        # build the state definition
        state_instance = State(
            **state_dict,
            config=config,
            persisted_position=count - 1,
        )

        return state_instance

    def load_state_columns(self, state_id: str):
        # rebuild the column definition
        return self.fetch_state_columns(state_id=state_id)

    def load_state_data(self, columns: dict):
        # rebuild the data values by column and values
        return {
            column: self.fetch_state_data_by_column_id(column_definition.id)
            for column, column_definition in columns.items()
            if not column_definition.value  # only return row data that is not a function or a constant
        }

    def load_state_data_mappings(self, state_id: str):

        # rebuild the data state mapping
        return self.fetch_state_column_data_mappings(
            state_id=state_id)

    def load_state(self, state_id: str):
        # basic state instance
        state = self.load_state_basic(state_id=state_id)

        if not state:
            return None

        # load additional details about the state
        state.columns = self.load_state_columns(state_id=state_id)
        state.data = self.load_state_data(columns=state.columns)
        state.mapping = self.load_state_data_mappings(state_id=state_id)

        return state

    def save_state(self, state: State):

        first_time = state.persisted_position <= 0

        # TODO needs revision as columns and structures may change, need a way to check for
        #  consistency similar to how it is done at the processor apply_column,apply_data functions
        if not self.incremental or first_time:
            state_id = self.insert_state(state=state)
            self.insert_state_config(state=state)
            self.insert_state_columns(state=state)
            self.insert_state_columns_data(state=state, incremental=False)
            self.insert_state_column_data_mapping(state=state)
            self.insert_state_primary_key_definition(state=state)
            self.insert_query_state_inheritance_key_definition(state=state)
            self.insert_remap_query_state_columns_key_definition(state=state)
            self.insert_template_columns_key_definition(state=state)
        else:

            state_id = self.create_state_id_by_state(state)

            # the incremental function returns the list of state keys that need to be applied
            primary_key_mapping_update_set = self.insert_state_columns_data(state=state, incremental=True)

            # insert any new primary key references, provided that it was merged by the previous call
            self.insert_state_column_data_mapping(state=state, state_key_mapping_set=primary_key_mapping_update_set)

            # only save the state if there were changes made, track by primary key updates from previous calls
            if primary_key_mapping_update_set:
                self.insert_state(state=state)

        return state_id
