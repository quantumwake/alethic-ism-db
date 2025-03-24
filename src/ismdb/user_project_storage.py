import logging as log
import datetime as dt
import uuid

from typing import Optional, List

from ismcore.model.base_model import UserProject
from ismcore.storage.processor_state_storage import UserProjectStorage
from ismdb.base import BaseDatabaseAccessSinglePool

logging = log.getLogger(__name__)


class UserProjectDatabaseStorage(UserProjectStorage, BaseDatabaseAccessSinglePool):

    def delete_user_project(self, project_id):
        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = """DELETE FROM user_project WHERE project_id = %s"""
                cursor.execute(sql, [project_id])
            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def fetch_user_project(self, project_id: str) -> Optional[UserProject]:
        return self.execute_query_one(
            "select * from user_project",
            conditions={
                "project_id": project_id
            },
            mapper=lambda row: UserProject(**row)
        )

    def associate_user_project(self, project_id: str, user_id: str):
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:

                sql = """
                    INSERT INTO user_project (project_id, user_id, created_date) 
                    VALUES (%s, %s, %s)
                    ON CONFLICT (project_id, user_id) 
                    DO NOTHING
                """

                values = [
                    project_id,
                    user_id,
                    dt.datetime.utcnow()
                ]
                cursor.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def insert_user_project(self, user_project: UserProject):
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:

                sql = """
                    INSERT INTO user_project (project_id, project_name, user_id, created_date) 
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (project_id) 
                    DO UPDATE SET project_name = EXCLUDED.project_name
                """

                # assign project id if project id is not assigned
                user_project.project_id = user_project.project_id if user_project.project_id else str(uuid.uuid4())

                values = [
                    user_project.project_id,
                    user_project.project_name,
                    user_project.user_id,
                    dt.datetime.utcnow()
                ]
                cursor.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

        return user_project

    def fetch_user_projects(self, user_id: str) -> List[UserProject]:
        return self.execute_query_many(
            "select * from user_project",
            conditions={
                "user_id": user_id
            },
            mapper=lambda row: UserProject(**row)
        )
