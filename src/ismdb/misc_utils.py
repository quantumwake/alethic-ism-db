import logging as log
from typing import Type

from ismcore.model.processor_state import StateConfig, StateConfigLM, State
from ismcore.utils import general_utils

logging = log.getLogger(__name__)


def create_state_id_by_config(config: StateConfig):
    state_config_type = type(config).__name__
    hash_string = f'{config.name}:{state_config_type}'

    if isinstance(config, StateConfigLM):
        user_template = config.user_template_id  # just a name not a path
        system_template = config.system_template_id  # just a name not a path
        hash_string = f'{hash_string}:{user_template}:{system_template}'

    return general_utils.calculate_uuid_based_from_string_with_sha256_seed(hash_string)


def create_state_id_by_state(state: State):
    if not state.id:
        return create_state_id_by_config(config=state.config)
    else:
        return state.id


def map_row_to_dict(cursor, row):
    """ Maps a single row to a dictionary using column names from the cursor. """
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))


def map_rows_to_dicts(cursor, rows):
    """ Maps a list of rows to a list of dictionaries using column names from the cursor. """
    return [map_row_to_dict(cursor, row) for row in rows]


def map_rows_to_types(cursor, rows, type_: Type):
    """ Maps a list of rows to a list of dictionaries using column names from the cursor. """
    return [type_(**map_row_to_dict(cursor, row)) for row in rows]


def map_dict_to_type(data: dict, type_: Type):
    return type_(**data)
