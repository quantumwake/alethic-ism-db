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
from core.processor_state import StateConfigLM, StateConfig
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
