import os
import random

from core.processor_state import State, StateConfigLM, InstructionTemplate, StateConfig, StateDataKeyDefinition, \
    ProcessorStatus
from core.processor_state_storage import Processor, ProcessorState
from core.utils.state_utils import validate_processor_status_change

from alethic_ism_db.db.processor_state_db_storage import ProcessorStateDatabaseStorage


DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres1@localhost:5432/postgres")


def create_mock_state() -> State:
    state = State(
        config=StateConfigLM(
            name="Test Language Model Configuration with Template",
            version="Test version 0.0.0",
            model_name="OpenAI",
            provider_name="gpt4",
            user_template_path="./test_templates/test_template_P1_user.json",
            system_template_path="./test_templates/test_template_P1_system.json"
        )
    )

    for i in range(5):

        for j in range(5):
            query_state = {
                "state_key": f"hello_world_state_key_{i}",
                "data": random.randbytes(64),
                "index": (j+1)*(i+1)
            }

            state.apply_columns(query_state=query_state)
            state.apply_row_data(query_state=query_state)

    return state


def create_mock_state_for_incremental_save() -> State:
    state = State(
        config=StateConfigLM(
            name="Test Language Model Configuration with Template",
            version="Test version 0.0.1",
            model_name="OpenAI",
            provider_name="gpt4",
            primary_key=[
                StateDataKeyDefinition(name="data")
            ],
            user_template_path="./test_templates/test_template_P1_user.json",
            system_template_path="./test_templates/test_template_P1_system.json"
        )
    )

    for i in range(0, 10):
        query_state = {
            "data": f"my data entry {i}",
            "index": f'{i}'
        }

        state.apply_columns(query_state=query_state)
        state.apply_row_data(query_state=query_state)

    return state

def create_mock_state_for_incremental_save_add_more_rows(state: State):
    for i in range(10, 20):
        query_state = {
            "data": f"my new data entry {i}",
            "index": f'{i}'
        }

        state.apply_columns(query_state=query_state)
        state.apply_row_data(query_state=query_state)

    return state


def create_mock_input_state() -> State:
    state = State(
        config=StateConfig(
            name="Test Me (Animals)",
            version="Test version 0.0",
            primary_key=[
                StateDataKeyDefinition(name="animal")
            ],
            query_state_inheritance=[
                StateDataKeyDefinition(name="animal")
            ],
            remap_query_state_columns=[         # TODO ??
                StateDataKeyDefinition(name="animal")
            ],
            template_columns=[                  # TODO ??
                StateDataKeyDefinition(name="animal")
            ]
        )
    )

    query_states = [
        {"animal": "cat"},
        {"animal": "dog"},
        {"animal": "pig"},
        {"animal": "cow"}
    ]

    for query_state in query_states:
        state.apply_columns(query_state=query_state)
        state.apply_row_data(query_state=query_state)

    return state


def create_mock_processor():
    # model = create_mock_model()
    db_storage = ProcessorStateDatabaseStorage(database_url=DATABASE_URL)

    processor = Processor(
        id="language/models/llama/13b-instruct",
        type="Llama2QuestionAnswerProcessor"
    )

    processor = db_storage.insert_processor(processor=processor)
    return processor

def create_mock_processor_state():
    mock_output_state = create_mock_state()
    mock_input_state = create_mock_input_state()

    storage = ProcessorStateDatabaseStorage(database_url=DATABASE_URL)
    input_state_id = storage.insert_state(state=mock_input_state)
    output_state_id = storage.insert_state(state=mock_output_state)

    processor = create_mock_processor()
    processor_state = ProcessorState(
        processor_id=processor.id,
        input_state_id=input_state_id,
        output_state_id=output_state_id,
        status=ProcessorStatus.CREATED
    )
    storage.update_processor_state(processor_state=processor_state)

    return processor_state

def test_incremental_save_state():

    def check(state1, state2):
        for row_index in range(state1.count):
            query0 = state1.get_query_state_from_row_index(index=row_index)
            query1 = state2.get_query_state_from_row_index(index=row_index)

            compare = {key: value for key, value in query0.items() if key not in query1 or value != query1[key]}
            assert not compare

    # add initial rows and check state consistency
    state = create_mock_state_for_incremental_save()
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

    template_dict = {
        "template_path": "instruction_template_P1_query_response_default_perspective_user_v8",
        "template_content": template_content,
        "template_type": "user_template"
    }

    storage = ProcessorStateDatabaseStorage(database_url=DATABASE_URL)
    storage.insert_template(
        template_path="test/hello_world",
        template_content=template_content,
        template_type="test_template")

    fetched_template = storage.fetch_template('test/hello_world')

    print(fetched_template)

def test_create_template():
    storage = ProcessorStateDatabaseStorage(database_url=DATABASE_URL)

    for i in range (10):
        instruction = InstructionTemplate(
            template_path=f"test/template/{i}",
            template_content="hello world {i}",
            template_type="user_template"
        )
        storage.insert_template(instruction_template=instruction)

    templates = [ x for x in storage.fetch_templates() if x.template_path.startswith('test/template/')]
    assert len(templates) == 10

    for template in templates:
        storage.delete_template(template_path=template.template_path)

    templates = [ x for x in storage.fetch_templates() if x.template_path.startswith('test/template/')]
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
    processor = create_mock_processor()
    assert processor.id is not None

    db_storage = ProcessorStateDatabaseStorage(database_url=DATABASE_URL)
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

    db_storage = ProcessorStateDatabaseStorage(database_url=DATABASE_URL)
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
    state = create_mock_state()

    assert state != None

    db_storage = ProcessorStateDatabaseStorage(database_url=DATABASE_URL)
    db_storage.save_state(state=state)


def test_state_config_lm():

    lm_new_state = create_mock_state()
    assert isinstance(lm_new_state.config, StateConfigLM)

    db_storage = ProcessorStateDatabaseStorage(database_url=DATABASE_URL)
    state_id = db_storage.save_state(state=lm_new_state)

    lm_load_state = db_storage.load_state(state_id=state_id)
    assert isinstance(lm_load_state.config, StateConfigLM)


def test_create_state():
    state1 = create_mock_state()
    state2 = create_mock_input_state()

    db_storage = ProcessorStateDatabaseStorage(database_url=DATABASE_URL)
    state_id_1 = db_storage.save_state(state=state1)
    state_id_2 = db_storage.save_state(state=state2)

    states = db_storage.fetch_states()
    states = [s for s in states if s['id'] in [state_id_1, state_id_2]]
    assert len(states) == 2

