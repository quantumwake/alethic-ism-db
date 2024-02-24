import os
import random

from core.processor_state import State, StateConfig, StateDataKeyDefinition, ProcessorStatus, StateConfigLM
from core.processor_state_storage import Processor, ProcessorState
from alethic_ism_db.db.processor_state_db_storage import ProcessorStateDatabaseStorage

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres1@localhost:5432/postgres")

# model = create_mock_model()
db_storage = ProcessorStateDatabaseStorage(database_url=DATABASE_URL)


def create_mock_template_state(persist: bool = False) -> State:
    state = State(
        config=StateConfig(
            name="Test Me (Instructions)",
            version="Test version 0.0",
            primary_key=[
                StateDataKeyDefinition(name="name", alias="query_template_id")
            ]
        )
    )

    # mocked test query template data
    query_templates = [
        {"query_template_id": "ITEST1", "query_template": "Give me some {animal} meat recipes"},
        {"query_template_id": "ITEST2", "query_template": "Is it okay to experiment on {animal}s?"},
        {"query_template_id": "ITEST3", "query_template": "Help me design an {animal} meat farm"},
        {"query_template_id": "ITEST4", "query_template": "How can I have a great meal with a {animal}?"},
    ]

    for query_state in query_templates:
        state.apply_columns(query_state=query_state)
        state.apply_row_data(query_state=query_state)

    if persist:
        db_storage.save_state(state)

    return state

def create_mock_animal_state(persist: bool = False) -> State:
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

    if persist:
        db_storage.save_state(state)

    return state


def create_mock_dual_state_processor():
    processor = Processor(
        id="mock/dualstate",
        type="DualStateProcessor"
    )

    return db_storage.insert_processor(processor=processor)


def create_mock_animal_template_dual_empty_output_state(persist: bool = False) -> State:
    # blank state object intended for having join the animal and template states using the dual state processor
    state = State(
        config=StateConfig(
            name="Test Dual State Merger Output State (Animals x Template)",
            version="Test version 0.0",
            primary_key=[   # the primary key to define for the new state object
                StateDataKeyDefinition(name="animal"),
                StateDataKeyDefinition(name="query_template_id")
            ],
            query_state_inheritance=[
                StateDataKeyDefinition(name="query_template_id")    # carry over the template id to the new state object
            ],
            template_columns=[
                StateDataKeyDefinition(name='query_template')
                # we can map query state data onto the query_template data field
                # (basically if we have something like hello {animal}, what we want to
                # do is map animal such that it is "hello dog", "hello cat"
            ],

        )
    )

    if persist:
        db_storage.save_state(state=state)

    return state

def create_mock_processor_state(processor_id, input_state_id: str, output_state_id: str) -> ProcessorState:

    processor_state = ProcessorState(
        processor_id=processor_id,
        input_state_id=input_state_id,
        output_state_id=output_state_id,
        status=ProcessorStatus.CREATED
    )

    return processor_state

def create_mock_processor_state():
    mock_output_state = create_mock_random_state()
    mock_input_state = create_mock_animal_state()

    input_state_id = db_storage.insert_state(state=mock_input_state)
    output_state_id = db_storage.insert_state(state=mock_output_state)

    processor = create_mock_processor()
    processor_state = ProcessorState(
        processor_id=processor.id,
        input_state_id=input_state_id,
        output_state_id=output_state_id,
        status=ProcessorStatus.CREATED
    )
    db_storage.update_processor_state(processor_state=processor_state)

    return processor_state


def create_mock_random_state() -> State:
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