from pydantic import BaseModel


class UserProfile(BaseModel):
    user_id: str


class UserProject(BaseModel):
    project_id: str
    project_name: str
    user_id: str


class WorkflowNode(BaseModel):
    node_id: str
    node_type: str
    node_label: str
    project_id: str
    object_id: str


class WorkflowEdge(BaseModel):
    source_node_id: str
    target_node_id: str
    edge_label: str

