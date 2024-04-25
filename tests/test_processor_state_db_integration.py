from core.base_model import InstructionTemplate, StatusCode
from core.processor_state import (
    StateConfigLM,
    State,
    StateConfig,
    StateDataKeyDefinition
)

from core.processor_state_storage import ProcessorState
from core.utils.state_utils import validate_processor_status_change
from alethic_ism_db.db.processor_state_db_storage import ProcessorStateDatabaseStorage, PostgresDatabaseStorage

from tests.mock_data import (
    DATABASE_URL,
    db_storage,
    create_mock_state_for_incremental_save,
    create_mock_state_for_incremental_save_add_more_rows,
    create_mock_processor_state_1,
    create_mock_random_state,
    create_mock_animal_state,
    create_mock_processor_provider, create_mock_processor_state_2
)


def test_state_key_definition_update():
    state_id = "00000000-0000-0000-0000-0000000000fe"

    state = State(
        id=state_id,
        config=StateConfig(
            name="hello world",
            primary_key=[
                StateDataKeyDefinition(
                    name="test key",
                    alias="test alias",
                    required=False,
                    callable=False
                )
            ]
        )
    )

    db_storage.delete_state_cascade(state_id=state_id)

    state = db_storage.save_state(state=state)
    assert state is not None
    state_id = state.id
    assert state.config.primary_key[0].id is not None

    loaded_state_1 = db_storage.load_state(state_id=state_id)
    assert loaded_state_1.config.primary_key[0].id is not None
    assert loaded_state_1.config.primary_key[0].name == state.config.primary_key[0].name
    assert loaded_state_1.config.primary_key[0].alias == state.config.primary_key[0].alias
    assert loaded_state_1.config.primary_key[0].required == state.config.primary_key[0].required
    assert loaded_state_1.config.primary_key[0].callable == state.config.primary_key[0].callable

    state.config.primary_key[0].required = True
    state.config.primary_key[0].callable = True
    state.config.primary_key[0].name = "test key updated"
    state.config.primary_key[0].alias = "test alias updated"

    state = db_storage.save_state(state=state)
    assert state is not None
    state_id = state.id

    loaded_state_2 = db_storage.load_state(state_id=state_id)
    assert len(loaded_state_2.config.primary_key) == 1
    assert loaded_state_2.config.primary_key[0].id is not None
    assert loaded_state_2.config.primary_key[0].id == state.config.primary_key[0].id
    assert loaded_state_2.config.primary_key[0].name == state.config.primary_key[0].name
    assert loaded_state_2.config.primary_key[0].alias == state.config.primary_key[0].alias
    assert loaded_state_2.config.primary_key[0].required == state.config.primary_key[0].required
    assert loaded_state_2.config.primary_key[0].callable == state.config.primary_key[0].callable



def test_state_with_id():
    state = State(
        id="53c7d78d-c90c-48c7-a397-bd4ae882aeb9",
        config=StateConfig(
            name="hello world",
            primary_key=[
                StateDataKeyDefinition(
                    name="test_key",
                    alias="test_alias",
                    required=True
                )
            ]
        )
    )

    saved_state = db_storage.save_state(state=state)
    loaded_state = db_storage.load_state(state_id=saved_state.id)

    assert saved_state.id == state.id
    assert loaded_state.id == saved_state.id
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
    storage = PostgresDatabaseStorage(database_url=DATABASE_URL, incremental=True)

    state = storage.save_state(state)
    loaded_state = storage.load_state(state_id=state.id)
    check(state1=state, state2=loaded_state)

    # add more rows and check again
    state = create_mock_state_for_incremental_save_add_more_rows(state=state)
    state = storage.save_state(state=state)

    # fetch and check data consistency
    loaded_state = storage.load_state(state_id=state.id)
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

    template = InstructionTemplate(**template_dict)
    template = db_storage.insert_template(template=template)
    fetched_template = db_storage.fetch_template(template.template_id)
    assert template_id == template.template_id

    print(fetched_template)


def test_create_template():
    for i in range (9):
        instruction = InstructionTemplate(
            template_id=f"b071c1ec-c6b7-4516-86c8-839458a0ed2{i}",
            template_path=f"test/template/{i}",
            template_content="hello world {i}",
            template_type="user_template"
        )
        db_storage.insert_template(template=instruction)

    templates = [x for x in db_storage.fetch_templates() if x.template_path.startswith('test/template/')]
    assert len(templates) == 9

    for template in templates:
        db_storage.delete_template(template_id=template.template_id)

    templates = [x for x in db_storage.fetch_templates() if x.template_path.startswith('test/template/')]
    assert len(templates) == 0


def test_create_processor():
    processor = create_mock_processor_state_1()
    assert processor.id is not None

    processors = db_storage.fetch_processors()
    processors = [proc for proc in processors if proc.id == processor.id]

    assert len(processors) == 1
    assert processors[0].id == processor.id
    assert processors[0].type == processor.type

    found_processor = db_storage.fetch_processor(processor_id=processor.id)
    assert found_processor is not None
    assert found_processor.id is not None

def test_create_processor_provider():
    provider = create_mock_processor_provider()
    providers = db_storage.fetch_processor_providers(user_id=provider.user_id)
    assert len(providers) == 1
    assert providers[0].id is not None
    assert providers[0].name == provider.name
    assert providers[0].version == provider.version
    assert providers[0].class_name == provider.class_name
    assert providers[0].user_id == provider.user_id
    assert providers[0].project_id == provider.project_id

    db_storage.delete_processor_provider(provider_id=provider.id)
    providers = db_storage.fetch_processor_providers(user_id=provider.user_id)
    assert len(providers) == 0


def test_create_processor_state():
    processor_state_1 = create_mock_processor_state_1()
    processor_state_2 = create_mock_processor_state_2()

    assert processor_state_1.processor_id is not None
    assert processor_state_2.processor_id is not None
    assert processor_state_1.processor_id == processor_state_2.processor_id

    # create the state and check whether the fetch works
    processor_states_list_1 = db_storage.fetch_processor_state(state_id=processor_state_1.state_id)
    processor_states_list_2 = db_storage.fetch_processor_state(state_id=processor_state_2.state_id)
    assert len(processor_states_list_1) == 1 and len(processor_states_list_2) == 1

    processor_states = db_storage.fetch_processor_state(processor_id=processor_state_1.processor_id)
    assert len(processor_states) == 2

    # delete and check whether it was deleted



def test_processor_state_transition():
    validate_processor_status_change(current_status=StatusCode.CREATED, new_status=StatusCode.QUEUED)
    validate_processor_status_change(current_status=StatusCode.QUEUED, new_status=StatusCode.RUNNING)
    validate_processor_status_change(current_status=StatusCode.RUNNING, new_status=StatusCode.TERMINATED)
    validate_processor_status_change(current_status=StatusCode.RUNNING, new_status=StatusCode.COMPLETED)

    try:
        validate_processor_status_change(
            current_status=StatusCode.TERMINATED,
            new_status=StatusCode.STOPPED
        )

        assert False is True
    except:
        assert True

    try:
        validate_processor_status_change(
            current_status=StatusCode.TERMINATED,
            new_status=StatusCode.FAILED
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

def test_create_state_update_state_details():
    state_json = {
        "id": "00000000-0000-0000-0000-0000000000ff",
        "state_type": "StateConfig",
        "config": {
            "name": "Test State 1",
            "storage_class": "database",
            "primary_key": [
                {
                    "name": "a",
                    "alias": "",
                    "required": True
                }
            ]
        }
    }

    state = State(**state_json)
    state_id = db_storage.save_state(state)
    loaded_state = db_storage.load_state(state_id=state_id)
    assert loaded_state.state_type == state.state_type
    assert loaded_state.config.name == state.config.name
    assert loaded_state.id == state.id

    loaded_state.config.name = "Test State 2"

    state_id = db_storage.save_state(loaded_state)
    loaded_state_again = db_storage.load_state(state_id=state_id)
    assert loaded_state.config.name == loaded_state_again.config.name


def test_create_state():
    state1 = create_mock_random_state()
    state2 = create_mock_animal_state()

    state_id_1 = db_storage.save_state(state=state1)
    state_id_2 = db_storage.save_state(state=state2)

    states = db_storage.fetch_states()
    # states = [s for s in states if s['id'] in [state_id_1, state_id_2]]
    assert len(states) == 2

