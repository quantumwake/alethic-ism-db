import logging as log
import datetime as dt
import uuid
from datetime import tzinfo
from http.cookiejar import UTC_ZONES

from typing import Optional, List

from ismcore.model.base_model import UserProject
from ismcore.storage.processor_state_storage import UserProjectStorage
from ismdb.base import BaseDatabaseAccessSinglePool
from ismdb.state_storage import StateDatabaseStorage

logging = log.getLogger(__name__)


class UserProjectDatabaseStorage(UserProjectStorage, BaseDatabaseAccessSinglePool):

    def soft_delete_project(self, project_id: str) -> int:
        """Soft delete a project by setting deleted_date"""
        deleted = self.execute_update(
            table="user_project",
            update_values={"deleted_date": dt.datetime.now()},
            conditions={"project_id": project_id})

        logging.info(f"soft deleted project {project_id}")
        return deleted

    def fetch_user_project(self, project_id: str) -> Optional[UserProject]:
        return self.execute_query_one(
            "select * from user_project",
            conditions={"project_id": project_id},
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
                    dt.datetime.now()
                ]
                cursor.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

        return user_project

    def fetch_user_projects(self, user_id: str, include_deleted: bool = False) -> List[UserProject]:
        conditions = {"user_id": user_id, "deleted_date": None} \
            if include_deleted else {"user_id": user_id}

        return self.execute_query_many(
            sql="select * from user_project",
            conditions=conditions,
            mapper=lambda row: UserProject(**row)
        )

    def fetch_deleted_projects(self, older_than_days: int = 30) -> List[UserProject]:
        """Fetch projects that have been soft deleted for more than specified days"""
        cutoff_date = dt.datetime.now() - dt.timedelta(days=older_than_days)
        sql = "select * from user_project WHERE deleted_date IS NOT NULL AND deleted_date < %s"
        return self.execute_query_fixed(
            sql=sql,
            params=["cutoff_date", cutoff_date],
            mapper=lambda row: UserProject(**row))
