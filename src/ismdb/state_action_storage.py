import uuid
import logging as log
from typing import Optional, List

from ismcore.model.base_model import StateActionDefinition
from ismcore.storage.processor_state_storage import StateActionStorage
from psycopg2._json import Json

from ismdb.base import BaseDatabaseAccessSinglePool

logging = log.getLogger(__name__)


class StateActionDatabaseStorage(BaseDatabaseAccessSinglePool, StateActionStorage):

    def create_state_action(self, action: StateActionDefinition) -> Optional[StateActionDefinition]:

        try:
            conn = self.create_connection()
            with (conn.cursor() as cursor):
                sql = """
                    INSERT INTO state_action_definition (
                        id,
                        state_id,
                        action_type,
                        field,
                        field_options,
                        remote_url,
                        created_date
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """

                if not action.id:
                    action.id = str(uuid.uuid4())

                cursor.execute(sql, [
                    action.id,
                    action.state_id,
                    action.action_type,
                    action.field,
                    Json(action.field_options),
                    action.remote_url,
                    action.created_date,
                ])

            conn.commit()
            return action
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def fetch_state_action(self, action_id: str) -> Optional[StateActionDefinition]:
        return self.execute_query_one(
            sql="select * from state_action_definition",
            conditions={
                'id': action_id
            },
            mapper=lambda row: StateActionDefinition(**row)
        )

    def fetch_state_actions(self, state_id: str) -> Optional[List[StateActionDefinition]]:
        return self.execute_query_many(
            sql="select * from state_action_definition where state_id = %s",
            conditions={
                'state_id': state_id
            },
            mapper=lambda row: StateActionDefinition(**row)
        )

    def delete_state_actions(self, state_id: str) -> int:
        return self.execute_delete_query(
            "delete from state_action_definition",
            conditions={
                "state_id": state_id
            }
        )

    def delete_state_action(self, action_id: str) -> int:
        return self.execute_delete_query(
            "delete from state_action_definition",
            conditions={
                "state_id": action_id
            }
        )

