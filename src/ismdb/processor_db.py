import ast
import logging as log
import math
import os
import json
import psycopg2

from typing import List, Any, Dict

from ismcore.embedding.embedding_utils import calculate_embeddings
from ismcore.model.processor_state import State, StateDataColumnDefinition, StateConfig, StateConfigLM, StateConfigDB, \
    StateDataKeyDefinition, implicit_count_with_force_count
from ismcore.processor.base_processor import BaseProcessor
from ismcore.utils.general_utils import clean_string_for_ddl_naming, higher_order_routine, load_yaml

# Read database URL from environment variable, defaulting to a local PostgreSQL database
# DATABASE_URL = os.environ.get("OUTPUT_DATABASE_URL", "postgresql://postgres:postgres1@localhost:5432/postgres")

logging = log.getLogger(__name__)


def build_query_state_embedding_from_columns(state: State = None, embedding_columns: dict = None):

    result_columns = {}

    # # fetch a list of keys "column names" from the current data entry (row)
    # search_key_mapping = {utils.build_column_name(key): key for key in state.columns.keys()}

    #
    def process(column_object: dict):

        if 'column' not in column_object:
            raise ValueError(f'column not defined as part of the column configuration setting '
                             f'specify both a column and name, where the column is the source '
                             f'column and the name is the target column')

        # otherwise create a new column derived from the target column name + prefixed with _embedding
        source_column_name = column_object['column']

        if 'name' not in column_object:
            target_column_embedding_name = f'{source_column_name}_embedding'
        else:
            target_column_embedding_name = column_object['name']

        def calculate_embedding_by_query_state(query_state: dict):
            if not query_state:
                raise Exception(f'invalid query state input, must be a valid key value pairing')

            if source_column_name not in query_state:
                logging.warning(f'unable to find source column {source_column_name} '
                                f'when creating source text embedding column')
                return None

            text_value = query_state[source_column_name]
            if not text_value:
                logging.warning(f'no value found for source column {source_column_name} in query state {query_state}')
                return None

            return calculate_embeddings(text_value)

        # create a new embedding function call
        # create a new column header with a higher order function to call when the data entry row is iterated over
        return {
            target_column_embedding_name: StateDataColumnDefinition.model_validate({
                'name': target_column_embedding_name,
                'source_column_name': source_column_name,
                'value': calculate_embedding_by_query_state,
                'data_type': 'vector',
                'dimensions': 384,
                'null': True
            })
        }

    # if the embedding columns is a function then invoke it
    # TODO pass in state information such that the function can create embedding columns (if needed)
    if callable(embedding_columns):
        embedding_columns = embedding_columns()

    if not embedding_columns:
        return result_columns

    # iterate list of columns to embed and create an embedding equivalent column
    for source_column_embedding_name in embedding_columns:
        new_column = process(source_column_embedding_name)

        if new_column:
            result_columns = {**result_columns, **new_column}

    return result_columns


def build_column_name(name: str):
    return clean_string_for_ddl_naming(name).lower()


def build_table_name(config: StateConfig):
    unique_name = config.name if config.name else None

    def prefix(name):
        _prefix = config.name.strip() if name else None

        if _prefix:
            return clean_string_for_ddl_naming(_prefix).lower()

        return str()

    if not unique_name and isinstance(config, StateConfigLM):
        provider = prefix(config.provider_name)
        model_name = prefix(config.model_name)
        user_template = prefix(config.user_template_path)
        system_template = prefix(config.system_template_path)

        table_name_appender_list = f"STATE_{provider} {model_name} {user_template} {system_template}".split()
        unique_name = "_".join([x for x in table_name_appender_list if x])

    return clean_string_for_ddl_naming(unique_name).lower()


def build_query_state_from_config(state: State, function_columns: callable):
    """

    :param state:
    :type function_columns: callable
    """

    config = state.config

    columns = {
        column_definition['name']: StateDataColumnDefinition.model_validate(
            column_definition
        )
        for column_definition in function_columns()
    }

    for column, column_definition in columns.items():
        column_definition.value = ast.literal_eval(column_definition.value)

    return columns


class BaseStateDatabaseProcessor(BaseProcessor):


    @property
    def config(self) -> StateConfigDB:
        return self.state.config

    @config.setter
    def config(self, config: StateConfigDB):
        self.state.config = config

    def embedding_columns(self):
        return self.config.embedding_columns

    def function_columns(self):
        return self.config.function_columns

    def constant_columns(self):
        return self.config.constant_columns
    # additional_values_func = None

    def __init__(self, state: State,
                 database_url: str,
                 processors: List[BaseProcessor] = None,
                 additional_values_func=None,
                 *args, **kwargs):

        super().__init__(state=state, processors=processors, **kwargs)
        # self.manager = ThreadQueueManager(num_workers=10)
        self.additional_values_func = additional_values_func
        self.database_url = database_url

    class SqlStatement:

        def __init__(self, sql: str, values: List[Any]):
            self.sql = sql
            self.values = values

    def create_column_ddl(self, column: StateDataColumnDefinition):
        if not column and not column.name:
            error = f'column_name does not exist in {column}'
            logging.error(error)
            raise Exception(error)

        column_name = column.name
        column_nullable = column.null
        column_type = column.data_type if column.data_type else 'str'

        min_length = column.min_length
        max_length = column.max_length

        # if the column name is key then use it as the primary key, otherwise there is no primary key
        # if 'key' == column_name.lower():
        #     primary_key = True
        #     ## TODO this is problematic since a response can have more than one output, thus having the same primary key value
        #     ## TODO in order to avoid dup keys in the processor logic, we need to add in a dynamic key hashing function such that
        #     ## it can use the output values as part of the key, not only the input values

        ## TODO we should probably use a DDL builder instead of this legaacy method

        # calculate the  highest value, base 2
        final_max_length = 0
        # cannot create a zero base of zero VARCHAR(0) zero field at least not
        # in this universe, he said facetiously while he contemplated existence
        if column.max_length:
            exponent = math.log2(max_length) + 1  # the log of the max size gives us the exponent
            final_max_length = int(math.pow(2, exponent))  # base 2 ^ exponent

        # if the max value is above the max allowed then use the text type instead (or clob)
        if column_type == 'vector':
            if not column.dimensions:
                raise Exception(f'column: {column_name} has no dimensions length, column type: {column_type}')
            dimensions = column.dimensions
            column_type = f'VECTOR({dimensions})'
        elif column_type is int:
            column_type = 'INTEGER'
        elif column_type is float:
            column_type = 'NUMBER'
        elif column_type is str and column.max_length and column.max_length < 1024:
            column_type = f"VARCHAR({final_max_length})"
        else:  # column_type is str:
            column_type = 'TEXT'

        column_name = clean_string_for_ddl_naming(column_name)

        return f'"{column_name}" {column_type} {"NULL" if column_nullable else "NOT NULL"}'

    def create_table_definition(self):

        # build the ddl for column
        columns = self.columns
        table_name = build_table_name(config=self.config)

        # create the column definitions based on the header column information
        # for each column header, invoke the create_column_ddl and returns a
        # list of columns which is then joined
        column_definitions = ',\n\t'.join([self.create_column_ddl(column=column_definition)
                                           for column_name, column_definition
                                           in columns.items()])

        return f"""
        CREATE EXTENSION IF NOT EXISTS vector;

        CREATE TABLE "{table_name}" (
        {column_definitions}
        );
        """.strip()

    def create_connection(self):
        return psycopg2.connect(self.database_url)

    def truncate_table(self, table_name: str):
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                cursor.execute(f'TRUNCATE TABLE {table_name}')
            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            conn.close()

    def create_table(self):
        ddl = self.create_table_definition()
        logging.debug(f'creating table: {ddl}')
        conn = self.create_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(ddl)
            conn.commit()
        except Exception as e:
            logging.warning(e)
            # raise e

    def drop_table(self, ddl: str = None):
        table_name = build_table_name(self.config)
        ddl = ddl if ddl else f'DROP TABLE IF EXISTS {table_name} '

        logging.debug(f'drop table: {ddl}')
        conn = self.create_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(ddl)
            conn.commit()
        except Exception as e:
            logging.warning(e)
            raise e

    def count_table(self, table_name: str):
        conn = self.create_connection()
        try:
            with conn.cursor() as cursor:
                result = cursor.execute(f'select count(*) as cnt from {table_name}')

            data = result
            return data['cnt']
        except Exception as e:
            logging.error(e)
            return None

    def write_state(self, input_query_state):

        def parse_column_name(col_name: str):
            return f'"{col_name}"'

        def parse_column_value(col_name: str, col_val: Any):
            # if not isinstance(col_val, str):
            raise NotImplementedError()
            # col_val = get_column_state_value(col_val, query_state=input_query_state)

            if not col_val:
                return None

            return f"{col_val}"

        # generate a list of columns by iterating through the list of keys
        column_names = ','.join([parse_column_name(column_name) for column_name in input_query_state.keys()])

        # generate the tuple(.., ..) of values by iterating through the list of columns
        column_values = tuple(parse_column_value(column_name, column_value)
                              for column_name, column_value
                              in input_query_state.items())

        # create column parameter indexes such that we can parameterize the inserts
        column_params = ','.join([f'%s' for idx in range(1, len(input_query_state.keys()) + 1)])

        # build table name from the current processor state
        table_name = f'"{build_table_name(self.config)}"'

        return self.SqlStatement(
            sql=f'INSERT INTO {table_name} ({column_names}) VALUES ({column_params})',
            values=column_values
        )

    # process the individual input query state
    def process_input_data_entry(self, input_query_state: dict, force: bool = False):
        sql_statement = self.write_state(input_query_state)
        try:
            print(sql_statement.sql)
            print(sql_statement.values)
            conn = self.create_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql_statement.sql, sql_statement.values)
            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e


class StateDatabaseProcessor(BaseStateDatabaseProcessor):

    def __call__(self,
                 state: State,
                 *args,
                 **kwargs):

        # initialize common information from the header (TODO this should be more generalized)
        if self.function_columns:
            additional_columns_function_higher_order_function = higher_order_routine(
                build_query_state_from_config,
                state=state,
                function_columns=self.function_columns)

        if self.constant_columns:
            logging.error(f'Constants are not implemented yet, I guess it should be easy to do? just copy the same thing from the functions and instead of evaluating with a higher level functiuon, just set the value. probably could have done it by now given the amount of typing here')
            # additional_columns_function_constants = higher_order_routine(
            #     build_query_state_from_config,
            #     state=state,
            #     function_columns=self.function_columns)

        if self.embedding_columns:
            additional_columns_function_embeddings = higher_order_routine(
                build_query_state_embedding_from_columns,
                state=state,
                embedding_columns=self.embedding_columns)

        # combine the additional columns added to the table
        def combined(*args, **kwargs):
            # NOTE: column response must return the value as well, it can also be a callable function
            additional_header_columns = additional_columns_function_higher_order_function(**kwargs)
            if self.embedding_columns:
                # when creating the embeddings, the value of the column is returned as function
                # this function takes the query_state and searches for columns specified in the config.embeddings_columns
                # if the field is found in the query state, it will pass it to an embedding model to create the word embeds
                additional_embedding_columns = additional_columns_function_embeddings(**kwargs)
                return {**additional_header_columns, **additional_embedding_columns}

            return additional_header_columns

        # step into the room of functions, said the "unfireable math guy".
        additional_columns_function = higher_order_routine(func=combined)

        # append all additional columns such that we can build the table definition
        combined_columns = additional_columns_function(state=state)

        # TODO this should be injected here not at the insertion/selector function
        state.columns = {**state.columns, **combined_columns}

        # this is the final state destination since it will be persisted into a database
        self.state = state

        # initialize the table

        self.create_table()

        # write the data to the db.
        # TODO fix this count issue ? maybe centralize it in the state only
        count = implicit_count_with_force_count(state=state)
        logging.info(f'starting processing loop with size {count} for state config {state.config}')

        # we need to generate the state keys
        for index in range(count):
            query_state = state.get_query_state_from_row_index(index)
            # self.process_input_data_entry(input_query_state=query_state)

            # setup a function call used to execute the processing of the actual entry
            process_func = higher_order_routine(self.process_input_data_entry,
                                                input_query_state=query_state)

            # add the entry to the queue for processing
            self.manager.add_to_queue(process_func)

        # wait on workers until the task is completed
        self.manager.wait_for_completion()

        # execute the downstream function to handle state propagation
        self.execute_downstream_processor_nodes()


def process_file(config: dict,
                 state: State = None,
                 state_file: str = None):

    if not state and not state_file:
        raise FileNotFoundError(f'Must specify either a state_file or a state input argument')
    elif state and state_file:
        raise AssertionError(f'Cannot specify state and state_file simultaneously')

    if state_file:
        state = State.load_state(state_file)

    database = config['database'] if 'database' in config else None
    if not database:
        raise KeyError(f'must specify database key and url in configuration or pass it in as an argument of db_url')

    # set the target database url (either from the config or as passed in argument, latter taking precedence)
    database_url = database['url']

    additional_columns = config["additional_columns"]

    #
    if additional_columns:

        # fetch configuration source columns to generate embedding vectors
        embedding_columns = additional_columns['embedding'] \
            if 'embedding' in additional_columns else None

        # fetch configuration source columns to generate values from functions
        function_columns = additional_columns['function'] \
            if 'function' in additional_columns else None

        # fetch configuration source columns to generate values from functions
        constant_columns = additional_columns['constant'] \
            if 'constant' in additional_columns else None

    else:
        embedding_columns = None
        function_columns = None
        constant_columns = None

    # extract the columns used for generating keys, if any
    key_definitions = config['key_definitions'] \
        if 'key_definitions' in config else None

    processor = StateDatabaseProcessor(
        database_url=database_url,
        state=State(
            config=StateConfigDB(
                name=state.config.name,
                embedding_columns=embedding_columns,
                function_columns=function_columns,
                constant_columns=constant_columns,
                output_primary_key_definition=[
                    StateDataKeyDefinition(name=name) for name in key_definitions
                ]
            )
        )
    )

    processor(state=state)
    return processor


def process_files(files: [str],
                  column_embedding: List[str] = None,
                  key_definitions: List[str] = None):

    return [process_file(state_file=file,
                         columns_embedding=column_embedding,
                         key_definitions=key_definitions)
            for file in files]


def process_file_by_config(config_file: str):

    if not os.path.exists(config_file):
        raise FileExistsError(f'unable to load configuration file {config_file}, file does not exist')

    if os.path.isdir(config_file):
        raise ImportError(f'unable to load configuration {config_file}, import directory, config-file must be a file not a directory')

    with open(config_file, 'r') as fio:
        config = json.load(fio)

    # fetch configuration source columns to generate embedding vectors
    embedding_columns = config['embedding_columns'] if 'embedding_columns' in config else None

    # extract the columns used for generating keys, if any
    key_definitions = config['key_definitions'] if 'key_definitions' in config else None

    # identify the state files to load
    state_sources = config['sources'] if 'sources' in config else None

    # iterate each state source
    for state_source in state_sources:

        logging.debug(f'processing state source: {state_source}')

        # recursive configured?
        recursive = state_source['recursive'] if 'recursive' in state_source else False

        # whether we should search for specific state names, within the state configuration header
        state_name_match = state_source['state_name_match'] if 'state_name_match' in state_source else None

        # whether we should look for a specific matching directory and or file names
        state_path_match = state_source['state_path_match'] if 'state_path_match' in state_source else None

        # fetch the path to search
        path = state_source['path'] if 'path' in state_source else None

        if not path:
            raise ImportError(f'path not specified in state source: {state_source}')



        raise NotImplemented() ## TODO
        #
        # state_files = find_state_files(search_path=path,
        #                                search_recursive=recursive,
        #                                state_name_match=state_name_match,
        #                                state_path_match=state_path_match)

        # if not state_files:
        #     logging.info(f'No state files found in path {path} using state source config {state_source}')
        #     continue

        # process individual files as defined in the configuration file
        return process_files(files=state_files,
                             column_embedding=embedding_columns,
                             key_definitions=key_definitions)



def process_file_by_config(
        states: Dict[str, State],
        config_file: str,
        database_url: str = None):

    if not os.path.exists(config_file):
        raise FileExistsError(f'unable to load configuration file {config_file}, file does not exist')

    if os.path.isdir(config_file):
        raise ImportError(f'unable to load configuration {config_file}, import directory, config-file must be a file not a directory')

    config = load_yaml(config_file)

    # iterate each state source
    for state_file, state in states.items():
        logging.debug(f'processing state: {state_file}')

        # process individual files as defined in the configuration file
        return process_file(state=state, config=config)


