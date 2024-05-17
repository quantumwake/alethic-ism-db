from typing import List
import logging

from core.base_model import StatusCode, ProcessorProvider
from core.base_processor_lm import BaseProcessorLM
from core.processor_state import State
from core.processor_state_storage import StateMachineStorage

logging = logging.getLogger(__name__)


class BaseDatabaseStorageProcessorLM(BaseProcessorLM):

    def __init__(self,
                 state_machine_storage: StateMachineStorage,
                 output_state: State,
                 provider: ProcessorProvider,
                 *args, **kwargs):

        super().__init__(state_machine_storage=state_machine_storage,
                         output_state=output_state,
                         **kwargs)

        self.provider = provider
        logging.info(f'extended instruction state machine: {type(self)} with config {self.config}')

    def update_current_status(self, new_status: StatusCode):
        raise NotImplemented()
        # self.processor_state.status = new_status
        # self.storage.update_processor_state(self.processor_state)

    def get_current_status(self):
        raise NotImplemented()
        # self.storage.fetch_processor_state()
        # return StatusCode.CREATED


        # current_state = self.storage.fetch_processor_states_by(
        #     processor_id=self.processor_state.processor_id,
        #     input_state_id=self.processor_state.input_state_id,
        #     output_state_id=self.processor_state.output_state_id
        # )
        # return current_state.status

