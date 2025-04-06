import uuid

from ismcore.model.base_model import UserProfileCredential

from tests.mock_data import (
    db_storage,
    create_user_profile,
    create_user_project1, create_user_project2, create_mock_workflow_nodes, create_user_project0,
    create_mock_workflow_two_basic_nodes, create_mock_workflow_two_basic_nodes_edges
)


def test_create_user_profile_credential():
    user = create_user_profile(user_id="d906504a-e421-42c8-af94-5a290d403db")
    credential = UserProfileCredential(user_id=user.user_id,type="password",credentials="test_password")
    db_storage.insert_user_profile_credential(credential)

    # Fetch the credential from the database
    fetched_credential = db_storage.fetch_user_profile_credential(user.user_id)
    assert fetched_credential is not None
    assert fetched_credential.user_id == user.user_id
    assert fetched_credential.type == "password"
    assert fetched_credential.credentials == "test_password"
