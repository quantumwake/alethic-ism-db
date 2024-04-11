from typing import Optional

from pydantic import BaseModel


class UserProfile(BaseModel):
    user_id: str


class UserProject(BaseModel):
    project_id: Optional[str] = None
    project_name: str
    user_id: str


class WorkflowNode(BaseModel):
    node_id: Optional[str] = None
    node_type: str
    node_label: Optional[str] = None
    project_id: str
    object_id: Optional[str] = None
    position_x: float
    position_y: float
    width: Optional[float] = None
    height: Optional[float] = None


class WorkflowEdge(BaseModel):
    source_node_id: str
    target_node_id: str
    source_handle: str
    target_handle: str
    edge_label: str
    animated: bool

