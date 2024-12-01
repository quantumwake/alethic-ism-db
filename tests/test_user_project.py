import uuid

from tests.mock_data import (
    db_storage,
    create_user_profile,
    create_user_project1, create_user_project2, create_mock_workflow_nodes, create_user_project0,
    create_mock_workflow_two_basic_nodes, create_mock_workflow_two_basic_nodes_edges
)


def test_user_projects():
    user = create_user_profile(user_id=str(uuid.uuid4()))
    project1 = create_user_project1(user_id=user.user_id, project_id=str(uuid.uuid4()))
    project2 = create_user_project2(user_id=user.user_id, project_id=str(uuid.uuid4()))

    project1 = db_storage.fetch_user_project(project_id=project1.project_id)
    project2 = db_storage.fetch_user_project(project_id=project2.project_id)

    assert project1.project_name == "Project Test 1"
    assert project2.project_name == "Project Test 2"

    projects = db_storage.fetch_user_projects(user_id=user.user_id)

    assert len(projects) == 2
    assert projects[0].project_name == project1.project_name
    assert projects[1].project_name == project2.project_name


def test_user_project_states():

    user = create_user_profile()
    project = create_user_project1(user.user_id)

    nodes, edges = create_mock_workflow_nodes(project_id=project.project_id)

    assert len(nodes) == 4
    fetched_nodes = db_storage.fetch_workflow_nodes(project_id=project.project_id)
    assert len(fetched_nodes) == len(nodes)

    fetched_edges = db_storage.fetch_workflow_edges(project_id=project.project_id)
    assert len(fetched_edges) == len(edges)


def test_user_project_delete():
    user = create_user_profile(user_id="ef775747-9789-416b-b291-b07ac696e935")
    project = create_user_project0(user_id=user.user_id, project_id="1cdd25ea-9b6d-4c26-a6ca-53f194d9a995")
    fetched_project = db_storage.fetch_user_project(project_id=project.project_id)

    assert project.project_name == fetched_project.project_name
    assert project.user_id == fetched_project.user_id

    db_storage.delete_user_project(project_id=fetched_project.project_id)

    fetched_project = db_storage.fetch_user_project(project_id=project.project_id)
    assert fetched_project is None


def test_create_user_project_nodes_and_edges_then_delete():
    user = create_user_profile(user_id="d906504a-e421-42c8-af94-5a290d403db")
    project = create_user_project0(user_id=user.user_id, project_id="60dc34fc-01ae-4b10-97cf-7dee4b593994")

    source_node, target_node = create_mock_workflow_two_basic_nodes(project_id=project.project_id)
    edge = create_mock_workflow_two_basic_nodes_edges(source_node.node_id, target_node.node_id)

    fetched_nodes = db_storage.fetch_workflow_nodes(project.project_id)
    assert len(fetched_nodes) == 2
    fetched_edges = db_storage.fetch_workflow_edges(project_id=project.project_id)
    assert len(fetched_edges) == 1

    # delete edge
    db_storage.delete_workflow_edge(source_node.node_id, target_node.node_id)
    fetched_edges = db_storage.fetch_workflow_edges(project_id=project.project_id)
    assert fetched_edges is None

    # delete nodes
    db_storage.delete_workflow_node(source_node.node_id)
    db_storage.delete_workflow_node(target_node.node_id)
    fetched_nodes = db_storage.fetch_workflow_nodes(project_id=project.project_id)
    assert fetched_nodes is None

    # delete project
    db_storage.delete_user_project(project_id=project.project_id)
    fetched_project = db_storage.fetch_user_project(project_id=project.project_id)
    assert fetched_project is None





