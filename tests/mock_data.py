import os
import random

from core.base_model import StatusCode, ProcessorStateDirection, UserProfile, UserProject, WorkflowNode, WorkflowEdge
from core.processor_state import State, StateConfig, StateDataKeyDefinition, StateConfigLM
from core.processor_state_storage import Processor, ProcessorState, ProcessorProvider

from alethic_ism_db.db.misc_utils import create_state_id_by_state
from alethic_ism_db.db.processor_state_db_storage import PostgresDatabaseStorage

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres1@localhost:5432/postgres")

# model = create_mock_model()
db_storage = PostgresDatabaseStorage(database_url=DATABASE_URL)


def create_mock_template_state(persist: bool = False) -> State:
    state = State(
        config=StateConfig(
            name="Test Me (Instructions)",
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
            primary_key=[
                StateDataKeyDefinition(name="animal")
            ],
            query_state_inheritance=[
                StateDataKeyDefinition(name="animal")
            ],
            remap_query_state_columns=[  # TODO ??
                StateDataKeyDefinition(name="animal")
            ],
            template_columns=[  # TODO ??
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
    provider = create_mock_processor_provider()

    processor = Processor(
        id="test/mock/testprocessor",
        provider_id=provider.id,
        project_id=provider.project_id,
        status=StatusCode.CREATED
    )

    return db_storage.insert_processor(processor=processor)


def create_mock_animal_template_dual_empty_output_state(persist: bool = False) -> State:
    # blank state object intended for having join the animal and template states using the dual state processor
    state = State(
        config=StateConfig(
            name="Test Dual State Merger Output State (Animals x Template)",
            primary_key=[  # the primary key to define for the new state object
                StateDataKeyDefinition(name="animal"),
                StateDataKeyDefinition(name="query_template_id")
            ],
            query_state_inheritance=[
                StateDataKeyDefinition(name="query_template_id")  # carry over the template id to the new state object
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


def create_mock_processor_provider():
    user_profile = create_user_profile()
    user_project = create_user_project0(user_id=user_profile.user_id)

    # create a processor provider and then remove it at the end
    provider = db_storage.insert_processor_provider(
        provider=ProcessorProvider(
            # id="test/something-1.0",
            name="Test",
            version="test-something-1.0",
            class_name="DataTransformation",
            user_id=user_profile.user_id,
            project_id=user_project.project_id
        )
    )

    return db_storage.insert_processor_provider(provider=provider)


def create_mock_processor():
    provider = create_mock_processor_provider()
    processor = Processor(
        id="faa25cd2-ce16-4bdb-9591-b326f4336872",
        provider_id=provider.id,
        project_id=provider.project_id,
        status=StatusCode.CREATED
    )
    return db_storage.insert_processor(processor=processor)


def create_mock_processor_state_base(state: State):
    processor = create_mock_processor()

    processor_state = ProcessorState(
        processor_id=processor.id,
        state_id=state.id,
        direction=ProcessorStateDirection.INPUT
    )

    return processor_state


def create_mock_processor_state_1() -> ProcessorState:
    mock_state_1 = create_mock_random_state()
    mock_state_1.id = "b7f5e802-3176-46f1-8120-fe9e4704f404"
    mock_state_1 = db_storage.insert_state(state=mock_state_1)
    processor_state = create_mock_processor_state_base(mock_state_1)
    processor_state.id = "c7e14344-3a1f-4cc1-8945-b726e226c860"
    processor_state = db_storage.insert_processor_state(processor_state=processor_state)
    return processor_state


def create_mock_processor_state_2() -> ProcessorState:
    mock_state_2 = create_mock_random_state()
    mock_state_2.id = "b7f5e802-3176-46f1-8120-fe9e4704f405"
    mock_state_2 = db_storage.insert_state(state=mock_state_2)
    processor_state = create_mock_processor_state_base(mock_state_2)
    processor_state.id = "c7e14344-3a1f-4cc1-8945-b726e226c861"
    processor_state = db_storage.insert_processor_state(processor_state=processor_state)
    return processor_state


def create_mock_random_state() -> State:
    state = State(
        config=StateConfigLM(
            name="Test Language Model Configuration with Template",
            user_template_id="./test_templates/test_template_P1_user.json",
            system_template_id="./test_templates/test_template_P1_system.json"
        )
    )

    for i in range(5):
        for j in range(5):
            query_state = {
                "state_key": f"hello_world_state_key_{i}",
                "data": random.randbytes(64),
                "index": (j + 1) * (i + 1)
            }

            state.apply_columns(query_state=query_state)
            state.apply_row_data(query_state=query_state)

    return state


def create_mock_state_for_incremental_save() -> State:
    state = State(
        config=StateConfigLM(
            name="Test Language Model Configuration with Template",
            primary_key=[
                StateDataKeyDefinition(name="data")
            ],
            user_template_id="./test_templates/test_template_P1_user.json",
            system_template_id="./test_templates/test_template_P1_system.json"
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


def create_user_profile(user_id: str = None) -> UserProfile:
    user_id = "f401db9b-50fd-4960-8661-de3e7c2f9092" if not user_id else user_id
    user_profile = UserProfile(
        user_id=user_id
    )

    return db_storage.insert_user_profile(user_profile=user_profile)


def create_user_project0(user_id: str, project_id: str = None) -> UserProject:
    uuid_str = "00000000-0000-0000-0000-00000000000a" if not project_id else project_id
    user_project = UserProject(
        project_id=uuid_str,
        project_name="Project Test 0",
        user_id=user_id
    )
    return db_storage.insert_user_project(user_project=user_project)


def create_user_project1(user_id: str) -> UserProject:
    uuid_str = "63c8c2ac-a021-44db-b8cd-8619a8e1c8fa"
    user_project = UserProject(
        project_id=uuid_str,
        project_name="Project Test 1",
        user_id=user_id
    )
    return db_storage.insert_user_project(user_project=user_project)


def create_user_project2(user_id: str) -> UserProject:
    uuid_str = "61ee1bbe-6e1a-4f18-b516-e06bb4e11cfb"
    user_project = UserProject(
        project_id=uuid_str,
        project_name="Project Test 2",
        user_id=user_id
    )
    return db_storage.insert_user_project(user_project=user_project)


def create_mock_workflow_nodes_animal_and_template(project_id: str, persist: bool = False):
    animal_state = create_mock_animal_state()
    template_state = create_mock_template_state()

    # TODO need to rethink this, since these are mutable states,
    #  the state id is generated based on a set of criteria
    animal_state_id = create_state_id_by_state(state=animal_state)
    template_state_id = create_state_id_by_state(state=template_state)

    # animal input state
    animal_state_node = WorkflowNode(
        node_id="100000000-0000-0000-0000-00000000001",
        node_type="state",
        node_label="Input Test Animal State",
        project_id=project_id,
        object_id=animal_state_id,
        position_x=0,
        position_y=0,
        height=123,
        width=321
    )

    # instruction template input state
    template_state_node = WorkflowNode(
        node_id="100000000-0000-0000-0000-00000000002",
        node_type="state",
        node_label="Input Test Instruction Template State",
        project_id=project_id,
        object_id=template_state_id,
        position_x=100,
        position_y=200,
        height=123,
        width=321
    )

    # persist the workflow nodes for the states
    if persist:
        db_storage.insert_workflow_node(node=animal_state_node)
        db_storage.insert_workflow_node(node=template_state_node)

    return animal_state_node, template_state_node


def create_mock_workflow_nodes_dual_state_merger_and_state(project_id: str, persist: bool = False):
    # setup a dual state merge processor node and then persist it
    dual_state_processor = create_mock_dual_state_processor()
    dual_state_merge_processor_node = WorkflowNode(
        node_id="200000000-0000-0000-0000-00000000000",
        node_type="processor_dual_state_merge",
        node_label="Test Dual Merge State Processor (Animal x Instruction Template)",
        project_id=project_id,
        object_id=dual_state_processor.id,
        position_x=300,
        position_y=150,
        height=123,
        width=321
    )
    db_storage.insert_workflow_node(node=dual_state_merge_processor_node)

    #
    # create a new output state for the dual state merger
    #
    animal_and_template_state_output = create_mock_animal_template_dual_empty_output_state()
    animal_and_template_state_output_id = create_state_id_by_state(animal_and_template_state_output)
    animal_and_template_state_output_node = WorkflowNode(
        node_id="200000000-0000-0000-0000-00000000001",
        node_type="state",
        node_label="Test Output State (Animal x Instruction Template)",
        project_id=project_id,
        object_id=animal_and_template_state_output_id,
        position_x=500,
        position_y=150,
        height=123,
        width=321
    )
    db_storage.insert_workflow_node(animal_and_template_state_output_node)

    return dual_state_merge_processor_node, animal_and_template_state_output_node


def create_mock_workflow_two_basic_nodes(project_id: str):
    test_node1 = WorkflowNode(
        node_id="200000000-aabb-0000-0000-0000000000a",
        node_type="state",
        node_label="Test Node 1",
        project_id=project_id,
        object_id="<test nothing>",
        position_x=0,
        position_y=0,
        height=123,
        width=321
    )

    test_node2 = WorkflowNode(
        node_id="200000000-aabb-0000-0000-0000000000b",
        node_type="state",
        node_label="Test Node 2",
        project_id=project_id,
        object_id="<test nothing>",
        position_x=0,
        position_y=0,
        height=123,
        width=321
    )

    test_node1 = db_storage.insert_workflow_node(test_node1)
    test_node2 = db_storage.insert_workflow_node(test_node2)

    return test_node1, test_node2


def create_mock_workflow_two_basic_nodes_edges(source_node_id: str, target_node_id: str):
    test_edge = WorkflowEdge(
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        source_handle="source-1",
        target_handle="target-1",
        edge_label="basic two node test edge",
        animated=False
    )

    return db_storage.insert_workflow_edge(test_edge)


def create_mock_workflow_nodes(project_id: str):

    # create the animal and instruction template state nodes (this includes the actual state object)
    animal_state_node, template_state_node = create_mock_workflow_nodes_animal_and_template(
        project_id=project_id, persist=True)

    # create the dual state processor node and it's output state node
    dual_state_processor_node, dual_state_processor_output_state_node = create_mock_workflow_nodes_dual_state_merger_and_state(
        project_id=project_id, persist=True)

    # connect the input state (animal) to the dual state merge processor
    edge_animal_to_dual_state_merger = WorkflowEdge(
        source_node_id=animal_state_node.node_id,
        target_node_id=dual_state_processor_node.node_id,
        source_handle="source_handle_1",
        target_handle="target_handle_1",
        animated=False,
        edge_label="Input Test Animal State => Dual State Merger (Animal x Template)"
    )

    # connect the input state (template) to the dual state merge processor
    edge_template_to_dual_state_merger = WorkflowEdge(
        source_node_id=template_state_node.node_id,
        target_node_id=dual_state_processor_node.node_id,
        source_handle="source_handle_1",
        target_handle="target_handle_1",
        animated=False,
        edge_label="Input Test Instruction Template State  => Dual State Merger (Animal x Template)"
    )

    # connect the dual state merger processor node to the output state node
    edge_dual_state_merger_to_dual_state_output_state = WorkflowEdge(
        source_node_id=dual_state_processor_node.node_id,
        target_node_id=dual_state_processor_output_state_node.node_id,
        source_handle="source_handle_1",
        target_handle="target_handle_1",
        animated=False,
        edge_label="Dual State Merger (Animal x Template) => "
                   "Dual State Merger Single Output State (Combined Animal & Template)"
    )

    db_storage.insert_workflow_edge(edge_animal_to_dual_state_merger)
    db_storage.insert_workflow_edge(edge_template_to_dual_state_merger)
    db_storage.insert_workflow_edge(edge_dual_state_merger_to_dual_state_output_state)

    nodes = [
        animal_state_node,
        template_state_node,
        dual_state_processor_node,
        dual_state_processor_output_state_node
    ]

    edges = [
        edge_animal_to_dual_state_merger,
        edge_template_to_dual_state_merger,
        edge_dual_state_merger_to_dual_state_output_state
    ]

    return nodes, edges
