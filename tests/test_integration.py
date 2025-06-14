import os
import time
import unittest

import pytest

from ismcore.utils.state_utils import validate_processor_status_change
from ismdb.postgres_storage_class import PostgresDatabaseStorage
from ismcore.model.base_model import (
    InstructionTemplate,
    ProcessorStatusCode,
    ProcessorProperty,
    MonitorLogEvent)

from ismcore.model.processor_state import (
    State,
    StateConfig,
    StateConfigLM,
    StateConfigStream,
    StateDataKeyDefinition,
    StateDataColumnDefinition)


from tests.mock_data import (
    DATABASE_URL,
    db_storage,
    create_mock_state_for_incremental_save,
    create_mock_state_for_incremental_save_add_more_rows,
    create_mock_processor_state_1,
    create_mock_random_state,
    create_mock_animal_state,
    create_mock_processor_provider, create_mock_processor_state_2, create_mock_processor, create_user_project0,
    create_user_profile,
    create_mock_processor_state_3
)

state_id = "fa000000-0000-0000-0000-0000000000fa"

# set the timezone to UTC for test cases
os.environ['TZ'] = 'UTC'
time.tzset()  # Note: This works on Unix-like systems


def test_state_config_stream():
    state_config_stream = StateConfigStream(
        name="test stream state",
        storage_class="stream",
        url="protocol://domain/{state_id}"
    )

    state = State(
        state_id="hello world, yet another random stream state",
        config=state_config_stream,
        state_type="StateConfigStream"
    )
    state.state_type = "StateConfigStream"


def test_state_key_definition_delete():
    state_id = "fa000000-0000-0000-0000-0000000000fa"
    db_storage.delete_state_cascade(state_id=state_id)

    state = State(
        id=state_id,
        config=StateConfig(
            name="hello world",
            primary_key=[
                StateDataKeyDefinition(
                    name="test key 1",
                    alias="test alias",
                    required=False,
                    callable=False
                ),
                StateDataKeyDefinition(
                    name="test key 2",
                    alias="test alias",
                    required=False,
                    callable=False
                )
            ],
            query_state_inheritance=[
                StateDataKeyDefinition(
                    name="test key test",
                    alias="test alias",
                    required=False,
                    callable=False
                )
            ]
        )
    )

    # check to make sure everything was saved correctly
    saved_state = db_storage.save_state(state=state)
    fetched_state = db_storage.load_state(state_id=state.id)
    assert len(fetched_state.config.primary_key) == 2
    assert len(fetched_state.config.query_state_inheritance) == 1

    # delete the first primary key and then check to make sure everything is loaded correctly
    count = db_storage.delete_state_config_key_definition(
        state_id=state.id,
        definition_type="primary_key",
        definition_id=fetched_state.config.primary_key[0].id
    )
    assert count == 1

    fetched_state = db_storage.load_state(state_id=state.id)
    assert len(fetched_state.config.primary_key) == 1
    assert len(fetched_state.config.query_state_inheritance) == 1

    # delete the first query_state_inheritance key definition, then check again to make sure things are loaded correctly
    count = db_storage.delete_state_config_key_definition(
        state_id=state.id,
        definition_type="query_state_inheritance",
        definition_id=fetched_state.config.query_state_inheritance[0].id
    )
    assert count == 1

    fetched_state = db_storage.load_state(state_id=state.id)
    assert len(fetched_state.config.primary_key) == 1
    assert not fetched_state.config.query_state_inheritance

    # delete now the final and last primary_key and everything should be returning None now, not even an empty list
    count = db_storage.delete_state_config_key_definition(
        state_id=state.id,
        definition_type="primary_key",
        definition_id=fetched_state.config.primary_key[0].id
    )
    assert count == 1

    fetched_state = db_storage.load_state(state_id=state.id)
    assert not fetched_state.config.primary_key
    assert not fetched_state.config.query_state_inheritance


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

class MyTestCase(unittest.TestCase):

    def test_incremental_save_without_primary_key(self):
        state = State(
            config=StateConfig(name="Test State")
        )

        state.persisted_position = -1
        state.apply_query_state(query_state={
            "test_column_1": "test value 1_1",
            "test_column_2": "test value 1_2"
        })
        state = db_storage.save_state(state=state)
        assert state is not None
        assert state.count == 1
        assert state.persisted_position == 0 # index
        assert state.data["test_column_1"].count == 1
        assert state.data["test_column_2"].count == 1

        state = db_storage.load_state(state_id=state.id, load_data=True)
        assert state is not None
        assert state.count == 1
        assert state.data["test_column_1"].count == 1
        assert state.data["test_column_2"].count == 1
        assert state.data["test_column_1"].values[0] == "test value 1_1"
        assert state.data["test_column_2"].values[0] == "test value 1_2"

        for idx in range(2, 5):
            state.apply_query_state(query_state={
                "test_column_1": f"test value {idx}_1",
                "test_column_2": f"test value {idx}_2"
            })


        state = db_storage.save_state(state=state)
        assert state is not None
        assert state.count == 4
        assert state.persisted_position == 3 # index

        state = db_storage.load_state(state_id=state.id, load_data=True)
        assert state is not None
        assert state.data["test_column_1"].count == 4
        assert state.data["test_column_2"].count == 4
        assert state.data["test_column_1"].values[0] == "test value 1_1"
        assert state.data["test_column_2"].values[0] == "test value 1_2"
        assert state.data["test_column_1"].values[1] == "test value 2_1"
        assert state.data["test_column_2"].values[1] == "test value 2_2"

        for idx in range(6, 10):
            state.apply_query_state(query_state={
                "test_column_1": f"test value {idx}_1",
                "test_column_2": f"test value {idx}_2"
            })

        state = db_storage.save_state(state=state)
        state = db_storage.load_state(state_id=state.id, load_data=True)
        assert state is not None





def test_incremental_save_state():
    def check(state1, state2):
        for row_index in range(state1.count):
            query0 = state1.build_query_state_from_row_data(index=row_index)
            query1 = state2.build_query_state_from_row_data(index=row_index)

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
    for i in range(9):
        instruction = InstructionTemplate(
            template_id=f"b071c1ec-c6b7-4516-86c8-839458a0ed2{i}",
            template_path=f"test/template/{i}",
            template_content="hello world {i}",
            template_type="user_template"
        )
        db_storage.insert_template(template=instruction)

    templates = db_storage.fetch_templates()
    assert templates is not None
    templates = [x for x in templates if x.template_path.startswith('test/template/')]
    assert len(templates) == 9

    # delete the templates
    for template in templates:
        db_storage.delete_template(
            template_id=template.template_id
        )

    templates = db_storage.fetch_templates()
    templates = [x for x in templates if x.template_path.startswith('test/template/')]
    assert not templates


def test_create_processor():
    # fix the ids to avoid interference with other tests
    processor = create_mock_processor(
        processor_id="ecd6cba5-a111-4698-9bbd-2c0186dff4e4",
        provider_id="ecd6cba5-a111-4698-9bbd-2c0186dff4e4"
    )

    assert processor.id is not None

    processors = db_storage.fetch_processors()
    processors = [proc for proc in processors if proc.id == processor.id]

    assert len(processors) == 1
    assert processors[0].id == processor.id
    assert processors[0].status == ProcessorStatusCode.CREATED
    assert processors[0].provider_id == processor.provider_id

    found_processor = db_storage.fetch_processor(processor_id=processor.id)
    assert found_processor is not None
    assert found_processor.id is not None


def test_create_processor_properties():
    processor = create_mock_processor(
        processor_id="ecd6cba5-a111-4698-9bbd-2c0186dff4e5",
        provider_id="ecd6cba5-a111-4698-9bbd-2c0186dff4e5"
    )

    assert processor.id is not None

    properties = [ProcessorProperty(processor_id=processor.id, name=f'name {index}', value=f'value {index}')
                  for index
                  in range(10)]
    saved_properties = db_storage.insert_processor_properties(properties=properties)

    assert len(saved_properties) == len(properties)

    loaded_properties = db_storage.fetch_processor_properties(processor_id=processor.id)
    for index in range(10):
        assert loaded_properties[index].processor_id == saved_properties[index].processor_id
        assert loaded_properties[index].name == saved_properties[index].name
        assert loaded_properties[index].value == saved_properties[index].value

    assert 1 == db_storage.delete_processor_property(processor_id=processor.id, name='name 0')
    assert 1 == db_storage.delete_processor_property(processor_id=processor.id, name='name 1')
    assert 1 == db_storage.delete_processor_property(processor_id=processor.id, name='name 2')
    assert 1 == db_storage.delete_processor_property(processor_id=processor.id, name='name 3')
    assert 1 == db_storage.delete_processor_property(processor_id=processor.id, name='name 4')

    loaded_processor = db_storage.fetch_processor(processor_id=processor.id)
    assert len(loaded_processor.properties) == 5

    loaded_properties = db_storage.fetch_processor_properties(processor_id=processor.id)
    assert len(loaded_properties) == 5
    for index in range(5, 10):
        assert f'name {index}' == loaded_properties[index - 5].name
        assert f'value {index}' == loaded_properties[index - 5].value

    assert 1 == db_storage.delete_processor_property(processor_id=processor.id, name='name 5')
    assert 1 == db_storage.delete_processor_property(processor_id=processor.id, name='name 6')
    assert 1 == db_storage.delete_processor_property(processor_id=processor.id, name='name 7')
    assert 1 == db_storage.delete_processor_property(processor_id=processor.id, name='name 8')
    assert 1 == db_storage.delete_processor_property(processor_id=processor.id, name='name 9')

    loaded_properties = db_storage.fetch_processor_properties(processor_id=processor.id)
    assert not loaded_properties


def test_fetch_processor_provider():
    provider = create_mock_processor_provider(
        project_id="cf482595-7bac-44fb-985c-7cd63c5f49cb",
        provider_id="cf482595-7bac-44fb-985c-7cd63c5f49cb",
        user_id="cf482595-7bac-44fb-985c-7cd63c5f49cb"
    )

    fetched_provider = db_storage.fetch_processor_provider(provider.id)
    assert fetched_provider.id == provider.id
    does_not_exist_provider = db_storage.fetch_processor_provider("does/not/exists/provider")
    assert does_not_exist_provider is None


def test_create_processor_provider():
    # fix the ids so it doesn't interfere with other test cases
    provider = create_mock_processor_provider(project_id="cf482595-7bac-44fb-985c-7cd63c5f49ca",
                                              provider_id="cf482595-7bac-44fb-985c-7cd63c5f49ca",
                                              user_id="cf482595-7bac-44fb-985c-7cd63c5f49ca")
    providers = db_storage.fetch_processor_providers(user_id=provider.user_id)
    assert len(providers) == 1
    assert providers[0].id is not None
    assert providers[0].name == provider.name
    assert providers[0].version == provider.version
    assert providers[0].class_name == provider.class_name
    assert providers[0].user_id == provider.user_id
    assert providers[0].project_id == provider.project_id

    db_storage.delete_processor_provider(user_id=provider.user_id, provider_id=provider.id)
    providers = db_storage.fetch_processor_providers(user_id=provider.user_id)
    assert providers is None


def test_create_processor_status_change_status():
    processor_state = create_mock_processor_state_3(processor_id="test_processor_uuid_id")

    saved_processor_state = db_storage.insert_processor_state_route(processor_state=processor_state)
    assert processor_state.internal_id > 0
    assert processor_state.status == saved_processor_state.status
    assert saved_processor_state.status == ProcessorStatusCode.CREATED

    fetched_processor_state_list = db_storage.fetch_processor_state_route(processor_id=processor_state.processor_id,
                                                                          state_id=processor_state.state_id)
    assert len(fetched_processor_state_list) == 1

    fetched_processor_state = fetched_processor_state_list[0]
    assert fetched_processor_state.status == ProcessorStatusCode.CREATED

    fetched_processor_state.status = ProcessorStatusCode.QUEUED
    saved_processor_state = db_storage.insert_processor_state_route(processor_state=fetched_processor_state)

    # check the status update
    fetched_processor_state_again_list = db_storage.fetch_processor_state_route(
        processor_id=processor_state.processor_id, state_id=processor_state.state_id)
    fetched_processor_state_again = fetched_processor_state_again_list[0]
    assert fetched_processor_state_again.status == ProcessorStatusCode.QUEUED


def test_static_columns_with_updated_columns_using_new_query_state():
    state_id = "1dc0dadf-81e2-4c4e-a315-3f20d8be4d3c"
    db_storage.delete_state_cascade(state_id=state_id)
    state = create_mock_random_state(state_id=state_id)

    state.columns = {
        "test_column_name": StateDataColumnDefinition(
            name="test_column_name",
            value="some constant value A",
            data_type="str",
            required=True,
            callable=False
        )
    }

    state = db_storage.save_state(state=state)

    state.columns = {
        "test_column_new_name": StateDataColumnDefinition(
            id=state.columns['test_column_name'].id,
            name="test_column_new_name",
            value="some constant value A new",
            data_type="str",
            required=True,
            callable=False
        )
    }

    state = db_storage.save_state(state=state, options={
        "force_update_column": True
    })

    fetched_state = db_storage.load_state(state_id=state_id, load_data=False)
    assert len(fetched_state.columns) == 1
    assert 'test_column_new_name' in fetched_state.columns
    column = fetched_state.columns['test_column_new_name']

    assert column.id is not None
    assert column.name == 'test_column_new_name'
    assert column.value == 'some constant value A new'
    assert column.data_type == 'str'
    assert column.required
    assert not column.callable

    # test the security of the id, make sure id cannot be changed for a different state id

    new_state_id = "1dc0dadf-81e2-4c4e-a315-3f20d8be4d3d"
    db_storage.delete_state_cascade(state_id=new_state_id)
    new_state = create_mock_random_state(state_id=new_state_id)

    # attempt to update the column of the previous state by using a new state id
    new_state.columns = {
        "test_column_new_name": StateDataColumnDefinition(
            id=fetched_state.columns['test_column_new_name'].id,
            name="hacking attempt test_column_new_name",
            value="hacking attempt some constant value A new",
            data_type="str",
            required=True,
            callable=False
        )
    }

    with pytest.raises(Exception) as exc_info:
        new_state = db_storage.save_state(state=new_state, options={
            "force_update_column": True
        })


def test_create_processor_state():
    # persist some processing input states
    processor_state_1 = create_mock_processor_state_1()
    processor_state_2 = create_mock_processor_state_2()

    assert processor_state_1.processor_id is not None
    assert processor_state_2.processor_id is not None
    assert processor_state_1.processor_id == processor_state_2.processor_id

    # create the state and check whether the fetch works
    processor_states_list_1 = db_storage.fetch_processor_state_route(state_id=processor_state_1.state_id)
    processor_states_list_2 = db_storage.fetch_processor_state_route(state_id=processor_state_2.state_id)
    assert len(processor_states_list_1) == 1 and len(processor_states_list_2) == 1
    assert processor_states_list_1[0].state_id == processor_state_1.state_id
    assert processor_states_list_2[0].state_id == processor_state_2.state_id

    processor_states = db_storage.fetch_processor_state_route(processor_id=processor_state_1.processor_id)
    assert len(processor_states) == 2

    # ensure count values are correctly persisted
    assert processor_states_list_1[0].count == 10
    assert processor_states_list_1[0].current_index == 1
    assert processor_states_list_1[0].maximum_index == 5

    # update the count values to ensure it updates correctly
    processor_states_list_1[0].count = 11
    processor_states_list_1[0].current_index = 5
    processor_states_list_1[0].maximum_index = 6

    saved_processor_state = db_storage.insert_processor_state_route(processor_state=processor_states_list_1[0])
    fetched_processed_state = db_storage.fetch_processor_state_route(processor_id=saved_processor_state.processor_id,
                                                                     state_id=saved_processor_state.state_id,
                                                                     direction=saved_processor_state.direction)

    assert fetched_processed_state[0].count == saved_processor_state.count
    assert fetched_processed_state[0].current_index == saved_processor_state.current_index
    assert fetched_processed_state[0].maximum_index == saved_processor_state.maximum_index


def test_processor_state_fetch_by_project_id():
    user = create_user_profile(user_id="processor_state_project_id")
    project = create_user_project0(user.user_id, "processor_state_project_id")
    state = create_mock_random_state(
        state_id="processor_state_fetch_project_id",
        project_id=project.project_id
    )

    user = db_storage.insert_user_profile(user_profile=user)
    project = db_storage.insert_user_project(project)
    state = db_storage.save_state(state=state)

    # create a mocked processor state connection
    processor_state = create_mock_processor_state_1(
        processor_id="processor_state_fetch_project_id",
        state_id=state.id,
        project_id=project.project_id
    )

    # fetch processor states on a project level
    processor_states = db_storage.fetch_processor_state_routes_by_project_id(
        project_id=project.project_id
    )

    assert len(processor_states) == 1



def test_create_state__data_and_delete_state_data():
    state = create_mock_random_state(state_id="34fce882-a168-47be-9750-b1d16a763e87", add_data=False)
    state.config.primary_key = [StateDataKeyDefinition(
        name="question"
    )]
    state = db_storage.save_state(state=state)
    assert state
    fetch_state = db_storage.load_state(state_id=state.id)

    # delete any previous state
    db_storage.delete_state_data(state_id=fetch_state.id)
    fetch_state = db_storage.load_state(state_id=fetch_state.id)
    assert fetch_state.count == 0

    # apply and save new data into state
    data = [
        {"question": "is the sky blue?"},
        {"question": "do animals eat?"},
        {"question": "can dogs sing?"}
    ]

    [fetch_state.apply_query_state(query_state=qs) for qs in data]  # apply the query states consecutively.
    db_storage.save_state(state=fetch_state)
    db_storage.update_state_count(state=fetch_state)

    # load state after having been saved, and check state consistency
    fetch_state = db_storage.load_state(state_id=fetch_state.id)
    assert fetch_state
    assert fetch_state.count == 3

    # delete state data again and check for complete removal
    db_storage.delete_state_data(state_id=state.id)
    fetch_state = db_storage.load_state(state_id=fetch_state.id)
    assert fetch_state.count == 0


def test_processor_state_transition():
    validate_processor_status_change(
        current_status=ProcessorStatusCode.CREATED,
        new_status=ProcessorStatusCode.QUEUED
    )

    validate_processor_status_change(
        current_status=ProcessorStatusCode.QUEUED,
        new_status=ProcessorStatusCode.RUNNING
    )

    validate_processor_status_change(
        current_status=ProcessorStatusCode.RUNNING,
        new_status=ProcessorStatusCode.TERMINATE
    )

    validate_processor_status_change(
        current_status=ProcessorStatusCode.RUNNING,
        new_status=ProcessorStatusCode.COMPLETED
    )

    try:
        validate_processor_status_change(
            current_status=ProcessorStatusCode.TERMINATE,
            new_status=ProcessorStatusCode.STOPPED
        )

        assert False is True
    except:
        assert True

    try:
        validate_processor_status_change(
            current_status=ProcessorStatusCode.TERMINATE,
            new_status=ProcessorStatusCode.FAILED
        )

        assert True
    except:
        assert False is True


def test_monitor_log_event_empty_data():
    log1 = MonitorLogEvent(
        log_type='test log type'
    )

    saved_log_1 = db_storage.insert_monitor_log_event(monitor_log_event=log1)
    assert saved_log_1.log_id
    assert saved_log_1.log_time


def test_monitor_log_event_with_exception_and_data():
    log2 = MonitorLogEvent(
        log_type='test log type',
        internal_reference_id=-10000,
        exception=str(ValueError(f'some validation error handled')),
        data='{ "some":" "data" }'
    )

    saved_log_2 = db_storage.insert_monitor_log_event(monitor_log_event=log2)
    assert saved_log_2.log_id
    assert saved_log_2.log_time

    fetched_logs = db_storage.fetch_monitor_log_events(reference_id=-10000)
    assert len(fetched_logs) > 0  # TODO this is going to keep increasing

    for log in fetched_logs:
        assert log.log_time
        delete_count = db_storage.delete_monitor_log_event(
            log_id=log.log_id
        )
        assert delete_count == 1


def test_state_persistence():
    state = create_mock_random_state()
    assert state is not None
    db_storage.save_state(state=state)


def test_state_config_lm():
    lm_new_state = create_mock_random_state()
    assert isinstance(lm_new_state.config, StateConfigLM)

    state = db_storage.save_state(state=lm_new_state)
    lm_load_state = db_storage.load_state(state_id=state.id)
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
    saved_state = db_storage.save_state(state)
    assert state.id == saved_state.id

    loaded_state = db_storage.load_state(state_id=saved_state.id)
    assert loaded_state.state_type == state.state_type
    assert loaded_state.config.name == state.config.name
    assert loaded_state.id == state.id

    loaded_state.config.name = "Test State 2"

    updated_state = db_storage.save_state(loaded_state)
    loaded_state_again = db_storage.load_state(state_id=updated_state.id)
    assert loaded_state.config.name == loaded_state_again.config.name


def test_create_state():
    user_profile = create_user_profile(user_id="e3a8d9d1-3d5b-482a-99fd-6bcf584249b2")
    user_project = create_user_project0(user_id=user_profile.user_id, project_id="e3a8d9d1-3d5b-482a-99fd-6bcf584249b2")

    state1 = create_mock_random_state(state_id="491c7f37-e329-4044-921e-868b3f9650da",
                                      project_id=user_project.project_id)

    state2 = create_mock_animal_state(state_id="491c7f37-e329-4044-921e-868b3f9650db",
                                      project_id=user_project.project_id)

    saved_state_1 = db_storage.save_state(state=state1)
    saved_state_2 = db_storage.save_state(state=state2)

    states = db_storage.fetch_states(project_id=user_project.project_id)
    # states = [s for s in states if s['id'] in [state_id_1, state_id_2]]
    assert len(states) == 2
