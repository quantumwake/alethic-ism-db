from tests.mock_data import (
    db_storage,
    create_user_profile,
    create_user_project1, create_user_project2, create_mock_workflow_nodes, create_user_project0,
    create_mock_workflow_two_basic_nodes, create_mock_workflow_two_basic_nodes_edges
)


def test_user_projects():
    user = create_user_profile()
    project1 = create_user_project1(user_id=user.user_id)
    project2 = create_user_project2(user_id=user.user_id)

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
    user = create_user_profile()
    project = create_user_project0(user.user_id)
    fetched_project = db_storage.fetch_user_project(project_id=project.project_id)

    assert project.project_name == fetched_project.project_name
    assert project.user_id == fetched_project.user_id

    db_storage.delete_user_project(project_id=fetched_project.project_id)

    fetched_project = db_storage.fetch_user_project(project_id=project.project_id)
    assert fetched_project is None


def test_create_user_project_nodes_and_edges_then_delete():
    user = create_user_profile()
    project = create_user_project0(user.user_id)

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





