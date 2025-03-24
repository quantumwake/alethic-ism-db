import logging as log
from typing import Optional, List

from ismcore.model.base_model import WorkflowNode, WorkflowEdge
from ismcore.storage.processor_state_storage import WorkflowStorage

from ismdb.base import BaseDatabaseAccessSinglePool

logging = log.getLogger(__name__)


class WorkflowDatabaseStorage(WorkflowStorage, BaseDatabaseAccessSinglePool):

    def delete_workflow_node(self, node_id):
        return self.execute_delete_query(
            sql="DELETE FROM workflow_node",
            conditions={"node_id": node_id}
        )

    def fetch_workflow_nodes(self, project_id: str) -> Optional[List[WorkflowNode]]:
        return self.execute_query_many(
            "select * from workflow_node",
            conditions={
                "project_id": project_id
            },
            mapper=lambda row: WorkflowNode(**row)
        )

    def insert_workflow_node(self, node: WorkflowNode) -> WorkflowNode:
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:

                sql = """
                           INSERT INTO workflow_node (
                                node_id, 
                                node_type, 
                                node_label, 
                                project_id, 
                                object_id, 
                                position_x, 
                                position_y, 
                                width, 
                                height)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (node_id) 
                           DO UPDATE SET 
                            node_label = EXCLUDED.node_label,
                            object_id=EXCLUDED.object_id,
                            node_type=EXCLUDED.node_type,
                            position_x=EXCLUDED.position_x,
                            position_y=EXCLUDED.position_y,
                            width=EXCLUDED.width,
                            height=EXCLUDED.height
                       """

                values = [
                    node.node_id,
                    node.node_type,
                    node.node_label,
                    node.project_id,
                    node.object_id,  # the actual object id used, based on the type of node this is
                    node.position_x,
                    node.position_y,
                    node.width,
                    node.height
                ]
                cursor.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

        return node

    def delete_workflow_edge(self, source_node_id: str, target_node_id: str):
        return self.execute_delete_query(
            sql="DELETE FROM workflow_edge",
            conditions={
                "source_node_id": source_node_id,
                "target_node_id": target_node_id
            }
        )

    def delete_workflow_edges_by_node_id(self, node_id: str):
        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = """DELETE FROM workflow_edge WHERE source_node_id = %s OR target_node_id = %s"""
                cursor.execute(sql, [node_id, node_id])
            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def fetch_workflow_edges(self, project_id: str) -> Optional[List[WorkflowEdge]]:
        sql = """
                SELECT * FROM workflow_edge
                WHERE source_node_id IN (
                    SELECT node_id FROM workflow_node WHERE project_id = %s
                )
                OR target_node_id IN (
                    SELECT node_id FROM workflow_node WHERE project_id = %s
                )
            """
        params = [project_id, project_id]
        return self.execute_query_fixed(sql, params, lambda row: WorkflowEdge(**row))

    def insert_workflow_edge(self, edge: WorkflowEdge) -> WorkflowEdge | None:
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:

                sql = """INSERT INTO workflow_edge (
                            source_node_id, 
                            target_node_id, 
                            source_handle, 
                            target_handle, 
                            animated, 
                            edge_label,
                            type)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (source_node_id, target_node_id) 
                           DO UPDATE SET 
                            animated = EXCLUDED.animated,
                            edge_label = EXCLUDED.edge_label
                       """

                values = [
                    edge.source_node_id,
                    edge.target_node_id,
                    edge.source_handle,
                    edge.target_handle,
                    edge.animated,
                    edge.edge_label,
                    edge.type
                ]
                cursor.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

        return edge
