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

import os
import random
import uuid
from typing import List

from core.processor_state import State, StateConfigLM, InstructionTemplate, StateConfig, StateDataKeyDefinition, \
    ProcessorStatus
from core.processor_state_storage import Processor, ProcessorState
from core.utils.state_utils import validate_processor_status_change

from alethic_ism_db.db.models import UserProfile, UserProject, WorkflowNode, WorkflowEdge
from tests.mock_data import db_storage, create_mock_animal_state, create_mock_template_state, \
    create_mock_dual_state_processor, create_mock_animal_template_dual_empty_output_state


def create_user_profile() -> UserProfile:

    uuid_str = "f401db9b-50fd-4960-8661-de3e7c2f9092"
    user_profile = UserProfile(
        user_id=uuid_str
    )

    return db_storage.insert_user_profile(user_profile=user_profile)



def create_user_project0(user_id: str) -> UserProject:
    uuid_str = "00000000-0000-0000-0000-00000000000a"
    user_project = UserProject(
        project_id = uuid_str,
        project_name = "Project Test 0",
        user_id = user_id
    )
    return db_storage.insert_user_project(user_project=user_project)


def create_user_project1(user_id: str) -> UserProject:
    uuid_str = "63c8c2ac-a021-44db-b8cd-8619a8e1c8fa"
    user_project = UserProject(
        project_id = uuid_str,
        project_name = "Project Test 1",
        user_id = user_id
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
    animal_state_id = db_storage.create_state_id_by_state(state=animal_state)
    template_state_id = db_storage.create_state_id_by_state(state=template_state)

    # animal input state
    animal_state_node = WorkflowNode(
        node_id="100000000-0000-0000-0000-000000000001",
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
        node_id="100000000-0000-0000-0000-000000000002",
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
        node_id="200000000-0000-0000-0000-000000000000",
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
    animal_and_template_state_output_id = db_storage.create_state_id_by_state(animal_and_template_state_output)
    animal_and_template_state_output_node = WorkflowNode(
        node_id="200000000-0000-0000-0000-000000000001",
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
        node_id="200000000-aabb-0000-0000-00000000000a",
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
        node_id="200000000-aabb-0000-0000-00000000000b",
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
        edge_label="Input Test Animal State => Dual State Merger (Animal x Template)"
    )

    # connect the input state (template) to the dual state merge processor
    edge_template_to_dual_state_merger = WorkflowEdge(
        source_node_id=template_state_node.node_id,
        target_node_id=dual_state_processor_node.node_id,
        edge_label="Input Test Instruction Template State  => Dual State Merger (Animal x Template)"
    )

    # connect the dual state merger processor node to the output state node
    edge_dual_state_merger_to_dual_state_output_state = WorkflowEdge(
        source_node_id=dual_state_processor_node.node_id,
        target_node_id=dual_state_processor_output_state_node.node_id,
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





