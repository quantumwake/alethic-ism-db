from typing import List
import logging

from core.base_processor import BaseProcessor, ThreadQueueManager
from core.base_question_answer_processor import BaseQuestionAnswerProcessor
from core.processor_state import State, ProcessorStatus
from core.processor_state_storage import ProcessorState, ProcessorStateStorage
from core.utils.general_utils import higher_order_routine

logging = logging.getLogger(__name__)


class BaseQuestionAnswerProcessorDatabaseStorage(BaseQuestionAnswerProcessor):

    @property
    def user_template(self):
        if self.user_template_path:
            template = self.storage.fetch_template(self.user_template_path)
            return template.template_content
        return None

    @property
    def system_template(self):
        if self.system_template_path:
            template = self.storage.fetch_template(self.system_template_path)
            return template.template_content
        return None

    def __init__(self,
                 state: State,
                 processor_state: ProcessorState,
                 processors: List[BaseProcessor] = None,
                 storage: ProcessorStateStorage = None,
                 *args, **kwargs):

        super().__init__(state=state, processors=processors, **kwargs)

        self.manager = ThreadQueueManager(num_workers=10, processor=self)
        self.save_state_manager = ThreadQueueManager(num_workers=1)
        self.processor_state = processor_state
        self.storage = storage
        logging.info(f'extended instruction state machine: {type(self)} with config {self.config}')

    def pre_state_apply(self, query_state: dict):
        return super().pre_state_apply(query_state=query_state)



    def post_state_apply(self, query_state: dict):
        query_state = super().post_state_apply(query_state=query_state)
        self.storage.save_state(state=self.state)

        #
        # # setup a function call used to execute the processing of the actual entry
        # process_func = higher_order_routine(self.storage.save_state,
        #                                     state=self.state)
        #
        # # add the entry to the queue for processing
        # self.manager.add_to_queue(process_func)



        # start the thread runner only when all the data has been added to the queue
    #
    # self.manager.start()
    #
    # # wait on workers until the task is completed
    # self.manager.wait_for_completion()


    def load_previous_state(self, force: bool = False):
        # do nothing since this was meant to be for loading previous state
        pass

    def build_state_storage_path(self):
        # TODO look into this, not sure if this is a decent method
        return (f'{self.config.name}'
                f':{self.config.version}'
                f':{type(self.config).__name__}'
                f':{self.provider_name}'
                f':{self.model_name}')

    def update_current_status(self, new_status: ProcessorStatus):
        self.processor_state.status = new_status
        self.storage.update_processor_state(self.processor_state)

    def get_current_status(self):
        current_state = self.storage.fetch_processor_states_by(
            processor_id=self.processor_state.processor_id,
            input_state_id=self.processor_state.input_state_id,
            output_state_id=self.processor_state.output_state_id
        )
        return current_state.status

