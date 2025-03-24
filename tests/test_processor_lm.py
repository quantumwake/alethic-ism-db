import os

import logging

from ismcore.model.base_model import UserProfile, UserProject, InstructionTemplate
from ismcore.model.processor_state import StateConfigLM, State, StateDataKeyDefinition
from ismcore.processor.base_processor_lm import BaseProcessorLM

from ismdb.postgres_storage_class import PostgresDatabaseStorage

logging.basicConfig(level=logging.DEBUG)
logging = logging.getLogger(__name__)

# database url
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres1@localhost:5432/postgres")
storage = PostgresDatabaseStorage(DATABASE_URL)


class TestProcessorLM(BaseProcessorLM):

    def _execute(self, user_prompt: str, system_prompt: str, values: dict):
        logging.debug(f'user_prompt: {user_prompt}')

        if user_prompt == 'Only provide the answer the following question: what color is the sky?':
            return "blue", str, "blue"
        elif user_prompt == 'Only provide the answer the following question: what color is grass?':
            return "green", str, "green"

        return values


def test_processor_lm():
    user_profile = UserProfile(
        user_id="b5a12170-f647-4932-80a6-499bebc3ef7f"
    )

    user_project = UserProject(
        project_id="b5a12170-f647-4932-80a6-499bebc3ef7f",
        project_name="Test Project #1",
        user_id="b5a12170-f647-4932-80a6-499bebc3ef7f"
    )

    user_template = InstructionTemplate(
        template_id="b5a12170-f647-4932-80a6-499bebc3ef7f",
        template_path="test/configlm/user_template",
        template_content="Only provide the answer the following question: {question}",
        project_id="b5a12170-f647-4932-80a6-499bebc3ef7f",
        template_type="User Template"
    )

    user_profile = storage.insert_user_profile(user_profile=user_profile)
    user_project = storage.insert_user_project(user_project=user_project)
    user_template = storage.insert_template(template=user_template)

    output_state = State(
        id="0fb3170d-3855-4b6f-8413-fddceb0fe464",
        config=StateConfigLM(
            name="Test Question Response Output State",
            storage_class="database",
            user_template_id=user_template.template_id,
            primary_key=[StateDataKeyDefinition(name="question",required=True)],
            query_state_inheritance=[StateDataKeyDefinition(name="question",required=True)]
        )
    )

    output_state = storage.insert_state(state=output_state)

    processor_lm = TestProcessorLM(
        state_machine_storage=storage,
        output_state=output_state
    )

    query_states = [
        {"question": "what color is the sky?"},
        {"question": "what color is grass?"}
    ]

    query_state_01 = processor_lm.process_input_data_entry(input_query_state=query_states[0])
    query_state_02 = processor_lm.process_input_data_entry(input_query_state=query_states[1])
