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
