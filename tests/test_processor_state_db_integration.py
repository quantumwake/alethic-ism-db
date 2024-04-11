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
import uuid

from core.processor_state import (
    StateConfigLM,
    InstructionTemplate,
    ProcessorStatus, State, StateConfig, StateDataKeyDefinition
)

from core.processor_state_storage import ProcessorState
from core.utils.state_utils import validate_processor_status_change
from alethic_ism_db.db.processor_state_db_storage import ProcessorStateDatabaseStorage

from tests.mock_data import (
    DATABASE_URL,
    db_storage,
    create_mock_state_for_incremental_save,
    create_mock_state_for_incremental_save_add_more_rows,
    create_mock_processor_state,
    create_mock_random_state,
    create_mock_animal_state
)


def test_state_with_id():
    state = State(
        id="53c7d78d-c90c-48c7-a397-bd4ae882aeb9",
        config=StateConfig(
            name="hello world",
            version="test version",
            primary_key=[
                StateDataKeyDefinition(
                    name="test_key",
                    alias="test_alias",
                    required=True
                )
            ]
        )
    )

    state_id = db_storage.save_state(state=state)
    loaded_state = db_storage.load_state(state_id=state_id)

    assert state_id == state.id
    assert loaded_state.state_type == state.state_type
    assert loaded_state.state_type == "StateConfig"


def test_incremental_save_state():

    def check(state1, state2):
        for row_index in range(state1.count):
            query0 = state1.get_query_state_from_row_index(index=row_index)
            query1 = state2.get_query_state_from_row_index(index=row_index)

            compare = {key: value for key, value in query0.items() if key not in query1 or value != query1[key]}
            assert not compare

    # add initial rows and check state consistency
    state = create_mock_state_for_incremental_save()

    # create a new incremental state storage class
    storage = ProcessorStateDatabaseStorage(database_url=DATABASE_URL, incremental=True)

    state_id = storage.save_state(state)
    loaded_state = storage.load_state(state_id=state_id)
    check(state1=state, state2=loaded_state)

    # add more rows and check again
    state = create_mock_state_for_incremental_save_add_more_rows(state=state)
    state_id = storage.save_state(state)

    # fetch and check data consistency
    loaded_state = storage.load_state(state_id=state_id)
    check(state1=state, state2=loaded_state)


def test_create_template_newlines():

    template_content = """{query}
    
```json
{
    "response": "[response text to query, in text format only]",
    "justification": "[short justification for your response]"
}
```"""

    template_id = "b071c1ec-c6b7-4516-86c8-839458a0ed24"
    template_dict = {
        "template_id": template_id,
        "template_path": "test/hello_world",
        "template_content": template_content,
        "template_type": "user_template",
        "project_id": None
    }

    template_id = db_storage.insert_template(**template_dict)
    fetched_template = db_storage.fetch_template(template_id)
    assert template_id == template_id

    print(fetched_template)

def test_create_template():

    for i in range (9):
        instruction = InstructionTemplate(
            template_id=f"b071c1ec-c6b7-4516-86c8-839458a0ed2{i}",
            template_path=f"test/template/{i}",
            template_content="hello world {i}",
            template_type="user_template"
        )
        db_storage.insert_template(instruction_template=instruction)

    templates = [x for x in db_storage.fetch_templates() if x.template_path.startswith('test/template/')]
    assert len(templates) == 9

    for template in templates:
        db_storage.delete_template(template_id=template.template_id)

    templates = [x for x in db_storage.fetch_templates() if x.template_path.startswith('test/template/')]
    assert len(templates) == 0


# def test_fetch_models():
#     db_storage = ProcessorStateDatabaseStorage(database_url=DATABASE_URL)
#     models = db_storage.fetch_models()
#     assert len(models) > 0
#
#
# def test_create_model():
#     db_storage = ProcessorStateDatabaseStorage(database_url=DATABASE_URL)
#
#     # create a mock model
#     model = create_mock_model()
#
#     assert model.id is not None
#     models = [m for m in db_storage.fetch_models()
#               if m.model_name == model.model_name
#               and m.provider_name == model.provider_name]
#
#     assert len(models) == 1


def test_create_processor():
    processor = create_mock_processor_state()
    assert processor.id is not None

    processors = db_storage.fetch_processors()
    processors = [proc for proc in processors if proc.id == processor.id]

    assert len(processors) == 1
    assert processors[0].id == processor.id
    assert processors[0].type == processor.type

    found_processor = db_storage.fetch_processor(processor_id=processor.id)
    assert found_processor is not None
    assert found_processor.id is not None


def test_create_processor_state():
    processor_state = create_mock_processor_state()
    assert processor_state.processor_id is not None

    processor_states = db_storage.fetch_processor_states()
    processor_states = [
        procstate for procstate in processor_states
        if procstate.processor_id == processor_state.processor_id
           and procstate.output_state_id == processor_state.output_state_id
           and procstate.input_state_id == processor_state.input_state_id
    ]

    assert len(processor_states) == 1

    processor_states_by = db_storage.fetch_processor_states_by(processor_state.processor_id)
    assert isinstance(processor_states_by, ProcessorState)


def test_processor_state_transition():
    validate_processor_status_change(current_status=ProcessorStatus.CREATED, new_status=ProcessorStatus.QUEUED)
    validate_processor_status_change(current_status=ProcessorStatus.QUEUED, new_status=ProcessorStatus.RUNNING)
    validate_processor_status_change(current_status=ProcessorStatus.RUNNING, new_status=ProcessorStatus.TERMINATED)
    validate_processor_status_change(current_status=ProcessorStatus.RUNNING, new_status=ProcessorStatus.COMPLETED)

    try:
        validate_processor_status_change(
            current_status=ProcessorStatus.TERMINATED,
            new_status=ProcessorStatus.STOPPED
        )

        assert False is True
    except:
        assert True

    try:
        validate_processor_status_change(
            current_status=ProcessorStatus.TERMINATED,
            new_status=ProcessorStatus.FAILED
        )

        assert True
    except:
        assert False is True


def test_state_persistence():
    state = create_mock_random_state()
    assert state != None
    db_storage.save_state(state=state)


def test_state_config_lm():

    lm_new_state = create_mock_random_state()
    assert isinstance(lm_new_state.config, StateConfigLM)

    state_id = db_storage.save_state(state=lm_new_state)
    lm_load_state = db_storage.load_state(state_id=state_id)
    assert isinstance(lm_load_state.config, StateConfigLM)

def test_create_state_json():
    state_json = {
        "id": "ba1340a6-d689-434e-b88a-ff4be3d17119",
        "state_type": "StateConfigLM",
        "config": {
            "name": "Test State 1",
            "version": "default version",
            "storage_class": "database",
            "primary_key": [
                {
                    "name": "a",
                    "alias": "",
                    "required": True
                },
                {
                    "name": "some_value_a",
                    "alias": "",
                    "required": True
                },
                {
                    "name": "some_value_f",
                    "alias": "",
                    "required": True
                }
            ],
            "query_state_inheritance": None,
            "remap_query_state_columns": None,
            "template_columns": None,
            "user_template_id": "4b0d20f7-d1d6-47ed-a214-93ba38607bac"
        }
    }

    state_object = State(**state_json)
    assert state_object.state_type == type(state_object.config).__name__

def test_create_state():
    state1 = create_mock_random_state()
    state2 = create_mock_animal_state()

    state_id_1 = db_storage.save_state(state=state1)
    state_id_2 = db_storage.save_state(state=state2)

    states = db_storage.fetch_states()
    states = [s for s in states if s['id'] in [state_id_1, state_id_2]]
    assert len(states) == 2

