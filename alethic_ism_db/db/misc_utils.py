import logging as log
from core.processor_state import StateConfigLM, StateConfig
from core.utils import general_utils

from .model import ProcessorState, ProcessorStatus

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


def validate_processor_state_from_created(processor_state: ProcessorState):
    new_status = processor_state.status

    if new_status not in [ProcessorStatus.CREATED,
                          ProcessorStatus.QUEUED,
                          ProcessorStatus.RUNNING,
                          ProcessorStatus.TERMINATED,
                          ProcessorStatus.STOPPED,
                          ProcessorStatus.FAILED]:
        logging.error(
            f'unable to transition {ProcessorStatus.CREATED} to {new_status} for processor_state: {processor_state}')
        return False

    return True


def validate_processor_state_from_queued(processor_state: ProcessorState):
    new_status = processor_state.status

    if new_status not in [ProcessorStatus.STOPPED,
                          ProcessorStatus.TERMINATED,
                          ProcessorStatus.RUNNING,
                          ProcessorStatus.QUEUED]:
        logging.error(
            f'unable to transition {ProcessorStatus.QUEUED} to {new_status} for processor_state: {processor_state}')
        return False

    return True


def validate_processor_state_from_running(processor_state: ProcessorState):
    new_status = processor_state.status

    if new_status not in [ProcessorStatus.RUNNING,
                          ProcessorStatus.STOPPED,
                          ProcessorStatus.TERMINATED,
                          ProcessorStatus.FAILED,
                          ProcessorStatus.COMPLETED]:
        logging.error(
            f'unable to transition {ProcessorStatus.RUNNING} to {new_status} for processor_state: {processor_state}')
        return False

    return True


def validate_processor_state_from_stopped(processor_state: ProcessorState):
    new_status = processor_state.status

    if new_status not in [ProcessorStatus.STOPPED,
                          ProcessorStatus.TERMINATED,
                          ProcessorStatus.FAILED]:
        logging.error(
            f'unable to transition {ProcessorStatus.RUNNING} to {new_status} for processor_state: {processor_state}')
        return False

    return True


def validate_processor_state_from_terminated(processor_state: ProcessorState):
    new_status = processor_state.status

    if new_status not in [ProcessorStatus.TERMINATED,
                          ProcessorStatus.FAILED]:
        logging.error(
            f'unable to transition {ProcessorStatus.RUNNING} to {new_status} for processor_state: {processor_state}')
        return False

    return True


def validate_processor_state_from_failed(processor_state: ProcessorState):
    new_status = processor_state.status

    if new_status not in [ProcessorStatus.FAILED]:
        logging.error(
            f'unable to transition {ProcessorStatus.RUNNING} to {new_status} for processor_state: {processor_state}')
        return False

    return True


def validate_processor_state_from_completed(processor_state: ProcessorState):
    new_status = processor_state.status

    if new_status not in [ProcessorStatus.COMPLETED,
                          ProcessorStatus.FAILED]:
        logging.error(
            f'unable to transition {ProcessorStatus.RUNNING} to {new_status} for processor_state: {processor_state}')
        return False

    return True
