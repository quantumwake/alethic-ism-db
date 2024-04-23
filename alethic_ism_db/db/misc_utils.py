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
import logging as log
from typing import Type

from core.processor_state import StateConfigLM, StateConfig, State
from core.utils import general_utils

logging = log.getLogger(__name__)


def create_state_id_by_config(config: StateConfig):
    state_config_type = type(config).__name__
    hash_string = f'{config.name}:{config.version}:{state_config_type}'

    if isinstance(config, StateConfigLM):
        provider = config.provider_name
        model_name = config.model_name
        user_template = config.user_template_path  # just a name not a path
        system_template = config.system_template_path  # just a name not a path
        hash_string = f'{hash_string}:{provider}:{model_name}:{user_template}:{system_template}'

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
