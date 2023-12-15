from typing import List, Any

import psycopg2
import logging as log

from core.processor_state import (
    State,
    StateDataKeyDefinition,
    StateConfigLM,
    StateConfig,
    StateDataColumnDefinition,
    StateDataRowColumnData,
    StateDataColumnIndex
)
from core.utils import general_utils

logging = log.getLogger(__name__)


def create_state_id_by_config(config: StateConfig):
    state_config_type = type(config).__name__
    hash_key = f'{config.name}:{config.version}:{state_config_type}'

    if isinstance(config, StateConfigLM):
        provider = config.provider_name
        model_name = config.model_name
        user_template = config.user_template_path  # just a name not a path
        system_template = config.system_template_path  # just a name not a path
        hash_key = f'{hash_key}:{provider}:{model_name}:{user_template}:{system_template}'

    hash_key = general_utils.calculate_hash(hash_key)
    return hash_key


class ProcessorStateDatabaseStorage:

    def __init__(self, database_url):
        self.database_url = database_url

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

    def create_state_id_by_state(self, state: State):
        return create_state_id_by_config(config=state.config)

    def create_connection(self):
        return psycopg2.connect(self.database_url)

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
            conn.close()

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
            conn.close()

    def fetch_states(self):

        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""
                select * from state
                """

                cursor.execute(sql, [])
                rows = cursor.fetchall()
                result = self.map_rows_to_dicts(cursor, rows) if rows else None

            return result
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            conn.close()

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
            conn.close()

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
            conn.close()

    def insert_state(self, state: State):
        conn = self.create_connection()

        # get the configuration type for this state
        state_id = create_state_id_by_config(config=state.config)
        result = self.fetch_state_by_state_id(state_id=state_id)

        try:
            with conn.cursor() as cursor:
                if not result:
                    state_type = type(state.config).__name__
                    hash_key = self.create_state_id_by_state(state=state)
                    sql = f"""insert into state (id, name, state_type, count, version) values (%s, %s, %s, %s, %s)"""
                    values = [hash_key,
                              state.config.name.strip(),
                              state_type,
                              state.count,
                              state.config.version.strip()]
                    cursor.execute(sql, values)
                else:
                    hash_key = result['id']

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            conn.close()

        return hash_key

    def fetch_state_config(self, state_id: str):

        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = f"""
                select * from state_config where state_id = %s 
                """
                cursor.execute(sql, [state_id])
                rows = cursor.fetchall()
                results = self.map_rows_to_dicts(cursor, rows) if rows else None
                results = {
                    attribute['attribute']: attribute['data']
                    for attribute in results
                }
            return results
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            conn.close()

    def insert_template(self,
                        template_path: str,
                        template_content: str,
                        template_type: str):

        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = """
                          MERGE INTO template AS target
                          USING (SELECT 
                                   %s AS template_path, 
                                   %s AS template_content, 
                                   %s AS template_type) AS source
                             ON target.template_path = source.template_path 
                          WHEN NOT MATCHED THEN 
                              INSERT (template_path, template_content, template_type)
                              VALUES (
                                   source.template_path, 
                                   source.template_content, 
                                   source.template_type)
                      """

                values = [
                    template_path,
                    template_content,
                    template_type,
                ]

                cursor.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            conn.close()

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
                    self.insert_template(template_path=template_path,
                                         template_content=template['template_content'],
                                         template_type=template_type)
                    return template_path
                else:
                    return None

            user_template_path = convert_template(config.user_template_path, "user_template")
            system_template_path = convert_template(config.system_template_path, "system_template")

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
                    "name": "user_template_path",
                    "data": user_template_path
                },
                {
                    "name": "system_template_path",
                    "data": system_template_path
                }
            ])

        # create a new state
        state_id = self.create_state_id_by_state(state=state)

        if not attributes:
            logging.info(f'no additional attributes specified for '
                         f'state_id: {state_id}, name: {state.config.name}, '
                         f'version: {state.config.version}')
            return

        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:

                sql = """
                          MERGE INTO state_config AS target
                          USING (SELECT 
                                   %s AS state_id, 
                                   %s AS attribute, 
                                   %s AS data) AS source
                             ON target.state_id = source.state_id 
                            AND target.attribute = source.attribute
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
            conn.close()

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
            conn.close()

        return hash_key

    def insert_state_columns_data(self, state: State):
        state_id = self.create_state_id_by_state(state)
        columns = self.fetch_state_columns(state_id)

        if not columns:
            logging.warning(f'no data found for state id: {state_id}, '
                            f'name: {state.config.name}, '
                            f'version: {state.config.version}')
            return

        conn = self.create_connection()

        try:

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

                    for data_index, data_value in enumerate(state.data[column].values):
                        values = [
                            column_id,
                            data_index,
                            data_value
                        ]
                        cursor.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            conn.close()

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
            conn.close()

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
            conn.close()

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
            conn.close()

    def insert_state_column_data_mapping(self, state: State):

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
            conn.close()

    def load_state_basic(self, state_id: str):
        state_dict = self.fetch_state_by_state_id(state_id=state_id)
        state_type = state_dict['state_type']

        # rebuild the key definitions
        primary_key = self.fetch_state_key_definition(
            state_id=state_id,
            definition_type="primary_key")

        query_state_inheritance = self.fetch_state_key_definition(
            state_id=state_id,
            definition_type="query_state_inheritance")

        # fetch list of attributes associated to this state, if any
        config_attributes = self.fetch_state_config(state_id=state_id)
        general_attributes = {
            "name": state_dict['name'],
            "version": state_dict['version'],
            "primary_key": primary_key,
            "query_state_inheritance": query_state_inheritance,
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

        # build the state definition
        state_instance = State(
            config=config,
            count=state_dict['count']
        )

        return state_instance

    def load_state_columns(self, state: State):
        state_id = self.create_state_id_by_state(state=state)

        # rebuild the column definition
        state.columns = self.fetch_state_columns(
            state_id=state_id)

        return state

    def load_state_data(self, state: State):

        # rebuild the data values by column and values
        state.data = {
            column: self.fetch_state_data_by_column_id(column_definition['id'])
            for column, column_definition in state.columns.items()
        }

        return state

    def load_state_data_mappings(self, state: State):
        state_id = self.create_state_id_by_state(state=state)

        # rebuild the data state mapping
        state.mapping = self.fetch_state_column_data_mappings(
            state_id=state_id)

        return state

    def load_state(self, state_id: str):
        # basic state instance
        state = self.load_state_basic(
            state_id=state_id)

        self.load_state_columns(state=state)
        self.load_state_data(state=state)
        self.load_state_data_mappings(state=state)

        return state

    def save_state(self, state: State):

        self.insert_state(state=state)
        self.insert_state_config(state=state)
        self.insert_state_columns(state=state)
        self.insert_state_columns_data(state=state)
        self.insert_state_column_data_mapping(state=state)
        self.insert_state_primary_key_definition(state=state)
        self.insert_query_state_inheritance_key_definition(state=state)
