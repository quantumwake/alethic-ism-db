from ismcore.model.base_model import StateActionDefinition

from tests import mock_data
from tests.mock_data import db_storage


def test_create_state_action():
    user_profile = mock_data.create_user_profile(user_id="aaaaaaaa-aaaa-aaaa-aaaa-test-profile")
    user_project = mock_data.create_user_project0(user_id=user_profile.user_id, project_id="aaaaaaaa-aaaa-aaaa-aaaa-test-project")

    user_profile = db_storage.insert_user_profile(user_profile=user_profile)
    assert user_profile.user_id is not None

    user_project = db_storage.insert_user_project(user_project=user_project)
    assert user_project.project_id is not None

    state = mock_data.create_mock_random_state(
        state_id="aaaaaaaa-aaaa-aaaa-aaaa-test-state00",
        project_id=user_project.project_id
    )

    state = db_storage.insert_state(state=state)
    assert state.id is not None

    state_action_definition = StateActionDefinition(
        state_id=state.id,
        action_type="slider",
        field="evaluation_score",
        field_options={
            "min": 0,
            "max": 100,
            "step": 1,
            "default": 50
        },
        remote_url=None,
    )

    state_action_definition = db_storage.create_state_action(action=state_action_definition)
    assert state_action_definition is not None

    loaded_state_action_definition = db_storage.fetch_state_action(action_id=state_action_definition.id)
    assert loaded_state_action_definition is not None
    assert loaded_state_action_definition.id == state_action_definition.id
    assert loaded_state_action_definition.state_id == state_action_definition.state_id
    assert loaded_state_action_definition.action_type == state_action_definition.action_type
    assert loaded_state_action_definition.field == state_action_definition.field
    assert loaded_state_action_definition.field_options == state_action_definition.field_options
    assert loaded_state_action_definition.remote_url == state_action_definition.remote_url
    assert loaded_state_action_definition.created_date is not None



