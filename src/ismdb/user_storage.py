import logging as log
import datetime as dt

from typing import Optional

from ismcore.model.base_model import UserProfile
from ismcore.storage.processor_state_storage import UserProfileStorage

from ismdb.base import BaseDatabaseAccessSinglePool

logging = log.getLogger(__name__)


class UserProfileDatabaseStorage(UserProfileStorage, BaseDatabaseAccessSinglePool):

    def fetch_user_profile(self, user_id: str) -> Optional[UserProfile]:
        users = self.execute_query_many(
            sql="select * from user_profile",
            conditions={"user_id": user_id},
            mapper=lambda row: UserProfile(**row)
        )
        return users[0] if users else None

    def insert_user_profile(self, user_profile: UserProfile):
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:

                sql = """
                    INSERT INTO user_profile (user_id, email, name, max_agentic_units, created_date) 
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) 
                    DO UPDATE SET 
                        email = EXCLUDED.email,
                        name = EXCLUDED.name
                """

                values = [
                    user_profile.user_id,
                    user_profile.email,
                    user_profile.name,
                    user_profile.max_agentic_units,
                    dt.datetime.utcnow()
                ]
                cursor.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

        return user_profile
