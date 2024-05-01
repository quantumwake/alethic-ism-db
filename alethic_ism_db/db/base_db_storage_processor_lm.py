from typing import List
import logging

from core.base_model import StatusCode
from core.base_processor import BaseProcessor, ThreadQueueManager
from core.base_question_answer_processor import BaseProcessorLM
from core.processor_state import State
from core.processor_state_storage import StateMachineStorage

logging = logging.getLogger(__name__)


class BaseDatabaseStorageProcessorLM(BaseProcessorLM):

    @property
    def user_template(self):
        if self.user_template_id:
            template = self.storage.fetch_template(self.user_template_id)
            return template.template_content
        return None

    @property
    def system_template(self):
        if self.system_template_id:
            template = self.storage.fetch_template(self.system_template_id)
            return template.template_content
        return None

    def __init__(self,
                 output_state: State,
                 # processor_state: ProcessorState,
                 processors: List[BaseProcessor] = None,
                 storage: StateMachineStorage = None,
                 *args, **kwargs):

        super().__init__(output_state=output_state, processors=processors, **kwargs)

        self.manager = ThreadQueueManager(num_workers=1, processor=self)
        # self.processor_state = processor_state
        self.storage = storage
        logging.info(f'extended instruction state machine: {type(self)} with config {self.config}')

    def pre_state_apply(self, query_state: dict):
        return super().pre_state_apply(query_state=query_state)

    def post_state_apply(self, query_state: dict):
        query_state = super().post_state_apply(query_state=query_state)
        self.storage.save_state(state=self.output_state)
    #
    # def load_previous_state(self, force: bool = False):
    #     # do nothing since this was meant to be for loading previous state
    #     pass

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

