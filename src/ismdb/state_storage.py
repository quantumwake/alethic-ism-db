import logging as log
import uuid

from typing import Any, Optional, Dict, List, Callable

from ismcore.model.processor_state import (
    # state
    State,
    StateDataRowColumnData,
    StateDataColumnDefinition,
    StateDataKeyDefinition,
    StateDataColumnIndex,
    # state configs
    BaseStateConfig,
    StateConfigVisual,
    StateConfigLM,
    StateConfigStream,
    StateConfig,
    StateConfigCode)
from ismcore.storage.processor_state_storage import StateStorage
from ismdb.base import BaseDatabaseAccessSinglePool
from ismdb.misc_utils import map_rows_to_dicts, create_state_id_by_state

logging = log.getLogger(__name__)


class StateDatabaseStorage(StateStorage, BaseDatabaseAccessSinglePool):

    def fetch_state_data_by_column_id(self, column_id: int, state_count: int, offset: int | None = None, limit: int = 1000) -> Optional[StateDataRowColumnData]:
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                if offset is None:
                    sql = f"select * from state_column_data where column_id = %s order by data_index"
                    cursor.execute(sql, [column_id])
                else:
                    sql = f"select * from state_column_data where column_id = %s and data_index >= %s and data_index < %s order by data_index"
                    cursor.execute(sql, [column_id, offset, offset + limit])

                rows = cursor.fetchall()
                # Sparse-to-dense conversion: use data_index to place values correctly
                if rows:
                    # When paginating, create array sized for the page, not full state_count
                    array_size = limit if offset is not None else state_count
                    values = [None] * array_size  # Initialize with None for all rows
                    for row in rows:
                        data_index = row[1]  # Actual row position
                        data_value = row[2]  # The value
                        # Adjust index by offset when paginating
                        adjusted_index = data_index - offset if offset is not None else data_index
                        values[adjusted_index] = data_value
                else:
                    array_size = limit if offset is not None else state_count
                    values = [None] * array_size  # Empty column still needs full size

                # Truncate from bottom if we exceed state_count boundaries (in-place deletion)
                if offset is not None:
                    max_rows_available = state_count - offset
                    if len(values) > max_rows_available:
                        del values[max_rows_available:]

                data = StateDataRowColumnData(
                    values=values,
                    count=state_count
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

    def fetch_state_config(self, state_id: str) -> dict | None:

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
                    source_column_name,
                    display_order)
                VALUES (
                    COALESCE(validate_column_id(%s, %s), nextval('state_column_id_seq'::regclass)),
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id, state_id)
                    DO UPDATE SET 
                        name = EXCLUDED.name, 
                        data_type = EXCLUDED.data_type,
                        required = EXCLUDED.required, 
                        callable = EXCLUDED.callable,
                        min_length = EXCLUDED.min_length,
                        max_length = EXCLUDED.max_length,
                        value = EXCLUDED.value,
                        display_order = EXCLUDED.display_order
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
                        column_definition.source_column_name,
                        column_definition.display_order
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
        persisted_position = state.persisted_position   # keep track and update at the end
        try:
            track_mapping = set()

            def create_batch_row(data_index, column_row_data):
                if column == 'state_key':
                    track_mapping.add(column_row_data)

                return [column_id, data_index, column_row_data]

            with (conn.cursor() as cursor):
                for column, header in columns.items():
                    if column not in state.data:
                        logging.warning(f'no data found for column {column}, '
                                        f'ignorable if column is a constant or function')
                        continue

                    column_id = header.id

                    # incrementally adding data in batches, instead of iterating the entire set again
                    if incremental:
                        data_count = len(state.data[column].values)
                        offset = state.persisted_position + 1
                        batch_size = 5000

                        while offset < data_count:
                            # Fix: use min() to properly limit batch size
                            end_index = min(offset + batch_size, data_count)

                            insert_batch = [
                                create_batch_row(
                                    data_index + offset,  # Correct: absolute index in full dataset
                                    column_row_data
                                )
                                for data_index, column_row_data in
                                enumerate(state.data[column].values[offset:end_index])
                            ]

                            cursor.executemany(
                                "INSERT INTO state_column_data (column_id, data_index, data_value) VALUES (%s, %s, %s)",
                                insert_batch
                            )

                            offset = end_index
                            persisted_position = end_index - 1
                        #
                        # offset = state.persisted_position + 1  # the last persisted position
                        # batch_size = 5000                      # maximum batch size
                        # while offset < data_count:
                        #     maximum_limit = max(offset + batch_size, data_count)
                        #
                        #     insert_batch = [
                        #         create_batch_row(data_index + offset, column_row_data)
                        #         for data_index, column_row_data in
                        #         enumerate(state.data[column].values[offset : maximum_limit])
                        #     ]
                        #
                        #     cursor.executemany(
                        #         "INSERT INTO state_column_data (column_id, data_index, data_value) VALUES (%s, %s, %s)",
                        #         insert_batch)
                        #     offset += batch_size
                        #
                    else:

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
                            """.strip()

                        track_mapping = None

                        for data_index, column_row_data in enumerate(state.data[column].values):
                            values = [
                                column_id,
                                data_index,
                                column_row_data
                            ]
                            cursor.execute(sql, values)
                            persisted_position = data_index

            state.persisted_position = persisted_position
            conn.commit()
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
                    return None

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


    def insert_generic_key_definition(
            self,
            state: 'State',
            key_definition_type: str,
            get_definitions_fn: Callable[['State'], Optional[List['StateDataKeyDefinition']]]
    ) -> Optional[List['StateDataKeyDefinition']]:

        if not isinstance(state.config, StateConfig):
            return []

        definitions = get_definitions_fn(state)
        if not definitions:
            logging.debug(
                f'No {key_definition_type} defined for state_id: {state.id}, name: {state.config.name}'
            )
            return None

        return self.insert_state_key_definition(
            state=state,
            key_definition_type=key_definition_type,
            definitions=definitions
        )

    def insert_state_primary_key_definition(self, state: State) \
            -> List[StateDataKeyDefinition] | None:
        return self.insert_generic_key_definition(
            state=state,
            key_definition_type='primary_key',
            get_definitions_fn=lambda s: getattr(s.config, 'primary_key', None)
        )

    def insert_state_join_key_definition(self, state: State) \
            -> List[StateDataKeyDefinition] | None:
        return self.insert_generic_key_definition(
            state=state,
            key_definition_type='state_join_key',
            get_definitions_fn=lambda s: getattr(s.config, 'state_join_key', None)
        )

    def insert_query_state_inheritance_key_definition(self, state: State) \
            -> List[StateDataKeyDefinition] | None:
        return self.insert_generic_key_definition(
            state=state,
            key_definition_type='query_state_inheritance',
            get_definitions_fn=lambda s: getattr(s.config, 'query_state_inheritance', None)
        )

    def insert_remap_query_state_columns_key_definition(self, state: State) \
            -> List[StateDataKeyDefinition] | None:
        return self.insert_generic_key_definition(
            state=state,
            key_definition_type='remap_query_state_columns',
            get_definitions_fn=lambda s: getattr(s.config, 'remap_query_state_columns', None)
        )

    def insert_template_columns_key_definition(self, state: State) \
            -> List[StateDataKeyDefinition] | None:
        return self.insert_generic_key_definition(
            state=state,
            key_definition_type='template_columns',
            get_definitions_fn=lambda s: getattr(s.config, 'template_columns', None)
        )


    def insert_state_key_definition(self, state: State, key_definition_type: str,
                                    definitions: List[StateDataKeyDefinition]) \
            -> List[StateDataKeyDefinition] | None:

        state_id = create_state_id_by_state(state=state)

        if not definitions:
            logging.info(
                f'no key definitions defined for state_id: {state_id}, key_definition_type: {key_definition_type}')
            return None

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

    def fetch_state_column_data_mappings(self, state_id, offset: int | None = None, limit: int = 1000) \
            -> Optional[Dict[str, StateDataColumnIndex]]:
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                if offset is None:
                    sql = f"select state_key, data_index from state_column_data_mapping where state_id = %s"
                    cursor.execute(sql, [state_id])
                else:
                    sql = f"select state_key, data_index from state_column_data_mapping where state_id = %s and data_index >= %s and data_index < %s"
                    cursor.execute(sql, [state_id, offset, limit])

                rows = cursor.fetchall()
                if not rows:
                    logging.debug(f'no mapping found for state_id: {state_id}')
                    return None

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
            return None

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

        state_join_keys = self.fetch_state_key_definition(
            state_id=state_id,
            definition_type="state_join_key")

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
            "state_join_key": state_join_keys,
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
        elif 'StateConfigStream' == state_type:
            config = StateConfigStream(
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
        return state

    # load the state columns by state id
    def load_state_columns(self, state_id: str) \
            -> Optional[Dict[str, StateDataColumnDefinition]]:

        # rebuild the column definition
        return self.fetch_state_columns(state_id=state_id)

    # load the state data by columns, with offset and limit if applied
    def load_state_data(self, columns: Dict[str, StateDataColumnDefinition], state_count: int, offset: int | None = None, limit: int = 1000) \
            -> Optional[Dict[str, StateDataRowColumnData]]:

        # rebuild the data values by column and values
        return {
            column: self.fetch_state_data_by_column_id(column_definition.id, state_count, offset=offset, limit=limit)
            for column, column_definition in columns.items()
            # if not column_definition.value  # TODO REMOVE since we now store all constant and expression values in .data[col].values[]  ...old: only return row data that is not a function or a constant
        }

    # rebuild the data state mapping
    def load_state_data_mappings(self, state_id: str, offset: int | None = None, limit: int = 1000)  \
            -> Optional[Dict[str, StateDataColumnIndex]]:
        return self.fetch_state_column_data_mappings(state_id=state_id, offset=offset, limit=limit)

    # load the state and all its details
    def load_state(self, state_id: str, load_data: bool = True, offset: int | None = None, limit: int = 1000):
        # Deprecation warning - only for full data loads (no pagination)
        if load_data and offset is None:
            logging.warning(
                f"Loading full state data is DEPRECATED for state_id: {state_id}. "
                "Use load_state_metadata() and lightweight mode instead. "
                "Full data loading will be removed in a future version."
            )

        # basic state instance
        state = self.load_state_basic(state_id=state_id)

        if not state:
            return None

        # load additional details about the state
        state.columns = self.load_state_columns(state_id=state_id)
        state.data = self.load_state_data(columns=state.columns, state_count=state.count, offset=offset, limit=limit) if load_data else {}
        state.mapping = self.load_state_data_mappings(state_id=state_id) if load_data else {}
        state.persisted_position = state.count - 1

        return state

    # load state metadata without loading actual data arrays (memory efficient)
    def load_state_metadata(self, state_id: str):
        """
        Load state metadata only, without loading actual column data.
        This is memory-efficient for incremental updates where you don't need existing data.

        Returns State with:
        - Basic metadata (id, project_id, state_type, count)
        - Configuration
        - Column definitions
        - Empty data arrays
        - persisted_position set correctly
        """
        # basic state instance
        state = self.load_state_basic(state_id=state_id)

        if not state:
            return None

        # load column definitions but NOT the actual data
        state.columns = self.load_state_columns(state_id=state_id)
        state.data = {}  # Empty - no data loaded
        state.mapping = {}  # Empty - no mappings loaded
        state.persisted_position = state.count - 1

        return state

    def fetch_state_data_chunk_for_export(self, state_id: str, offset: int, limit: int):
        """
        Fetch a chunk of state data directly from the database for export purposes.
        Returns rows in the format: (column_name, data_index, data_value)

        This method is optimized for streaming large datasets without loading
        everything into memory at once.

        :param state_id: The ID of the state to export
        :param offset: Starting row index for this chunk
        :param limit: Maximum number of rows to fetch
        :return: List of tuples (column_name, data_index, data_value)
        """
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                # Query chunk using the state_column view
                sql = """
                    SELECT sc.name, sd.data_index, sd.data_value
                    FROM state_column sc
                    LEFT JOIN state_column_data sd ON sc.id = sd.column_id
                    WHERE sc.state_id = %s
                      AND sd.data_index >= %s
                      AND sd.data_index < %s
                    ORDER BY sd.data_index, sc.name
                """
                cursor.execute(sql, [state_id, offset, offset + limit])

                # Fetch all rows for this chunk
                rows = cursor.fetchall()
                return rows

        except Exception as e:
            logging.error(f"Error fetching state data chunk: {e}")
            raise e
        finally:
            self.release_connection(conn)

    # append data directly without loading existing data (memory efficient)
    def append_state_data_direct(self, state_id: str, query_states: List[Dict],
                                scope_variable_mappings: dict = None, batch_size: int = 5000):
        """
        Append new rows directly to the database without loading existing data.
        This is memory-efficient for incremental updates.

        Args:
            state_id: The state ID to append data to
            query_states: List of dictionaries containing the new rows to append (raw, will be transformed)
            scope_variable_mappings: Variables for evaluating callable columns in transformations
            batch_size: Number of rows to insert per batch (default 5000)

        Returns:
            Updated state metadata (count and persisted_position updated)
        """
        if not query_states:
            logging.warning(f'no query states provided for state_id: {state_id}')
            return None

        # Load only metadata (no data arrays)
        state = self.load_state_metadata(state_id=state_id)

        if not state:
            logging.error(f'state not found: {state_id}')
            return None

        # Transform query_states using state transformations (callable columns, primary keys, etc.)
        # but don't store in arrays (skip_data_append=True)
        # This will also create columns dynamically if they don't exist yet
        transformed_query_states = []
        for entry in query_states:
            transformed = state.apply_query_state(
                query_state=entry,
                skip_data_append=True,  # Skip appending to in-memory arrays
                scope_variable_mappings=scope_variable_mappings or {}
            )
            transformed_query_states.append(transformed)

        # Use the transformed data for insertion
        query_states = transformed_query_states

        # After transformations, state.columns should be populated (either from DB or dynamically created)
        columns = state.columns
        if not columns:
            logging.error(f'no columns found for state_id: {state_id} even after applying query_states')
            return None

        # Save the column definitions to database if this is a new state
        if columns:
            self.insert_state_columns(state=state, force_update=False)

        conn = self.create_connection()
        try:
            # Begin explicit transaction
            conn.autocommit = False

            track_mapping_set = set()

            # Calculate starting position for new data
            start_position = state.persisted_position + 1

            with conn.cursor() as cursor:
                # Start transaction explicitly
                cursor.execute("BEGIN")
                # Process each column separately with batched inserts
                for column_name, column_def in columns.items():
                    column_id = column_def.id

                    # Build batch of (column_id, data_index, value) for this column across all rows
                    column_batch = []
                    for row_offset, query_state in enumerate(query_states):
                        data_index = start_position + row_offset
                        column_value = query_state.get(column_name, None)

                        # Track state_key for mappings
                        if column_name == 'state_key' and column_value:
                            track_mapping_set.add(column_value)

                        column_batch.append([column_id, data_index, column_value])

                    # Batch insert all rows for this column with ON CONFLICT handling
                    # ON CONFLICT works with executemany in psycopg2
                    if column_batch:
                        cursor.executemany(
                            """
                            INSERT INTO state_column_data (column_id, data_index, data_value)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (column_id, data_index)
                            DO UPDATE SET data_value = EXCLUDED.data_value
                            """,
                            column_batch
                        )

                # Batch insert state mappings
                if track_mapping_set:
                    mapping_batch = []
                    for row_offset, query_state in enumerate(query_states):
                        if 'state_key' in query_state and query_state['state_key']:
                            state_key = query_state['state_key']
                            data_index = start_position + row_offset
                            mapping_batch.append([state_id, state_key, data_index])

                    if mapping_batch:
                        for mapping in mapping_batch:
                            cursor.execute(
                                """
                                MERGE INTO state_column_data_mapping AS target
                                USING (SELECT %s AS state_id, %s AS state_key, %s AS data_index) AS source
                                   ON target.state_id = source.state_id
                                  AND target.state_key = source.state_key
                                  AND target.data_index = source.data_index
                                WHEN NOT MATCHED THEN
                                    INSERT (state_id, state_key, data_index)
                                    VALUES (source.state_id, source.state_key, source.data_index)
                                """,
                                mapping
                            )

                # Update state count and persisted_position
                new_count = state.count + len(query_states)
                new_persisted_position = new_count - 1

                cursor.execute(
                    "UPDATE state SET count = %s WHERE id = %s",
                    [new_count, state_id]
                )

            conn.commit()

            # Update state object
            state.count = new_count
            state.persisted_position = new_persisted_position

            logging.info(f'appended {len(query_states)} rows to state {state_id}, new count: {new_count}')

            return state

        except Exception as e:
            logging.error(f'error appending data to state {state_id}: {e}')
            conn.rollback()
            raise e
        finally:
            self.release_connection(conn)

    # delete cascade the state and all its details
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
            conditions={
                "id": column_id,
                "state_id": state_id
            })

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
        state.persisted_position = state.count - 1
        return state

    def save_state(self, state: State, options: dict = None) -> State:

        def fetch_option(name: str, default: Any = None):
            if not options:
                return default

            return options[name] if name in options else default

        force_update_column = fetch_option('force_update_column', False)
        force_update_count = fetch_option('force_update_count', True)
        first_time = state.persisted_position < 0
        if not self.incremental or first_time:
            state = self.insert_state(state=state)
            self.insert_state_config(state=state)
            self.insert_state_columns(state=state, force_update=force_update_column)
            self.insert_state_columns_data(state=state, incremental=False)
            self.insert_state_column_data_mapping(state=state)
            self.insert_state_primary_key_definition(state=state)
            self.insert_state_join_key_definition(state=state)
            self.insert_query_state_inheritance_key_definition(state=state)
            self.insert_remap_query_state_columns_key_definition(state=state)
            self.insert_template_columns_key_definition(state=state)
            if force_update_count:
                self.update_state_count(state=state)
        else:
            # the incremental function returns the list of state keys that need to be applied
            primary_key_mapping_update_set = self.insert_state_columns_data(state=state, incremental=True)

            # insert any new primary key references, provided that it was merged by the previous call
            self.insert_state_column_data_mapping(state=state, state_key_mapping_set=primary_key_mapping_update_set)

            # only save the state if there were changes made, track by primary key updates from previous calls
            if primary_key_mapping_update_set:
                self.insert_state(state=state)

            # update state count
            if force_update_count:
                self.update_state_count(state=state)

        return state
