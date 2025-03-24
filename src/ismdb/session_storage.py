import logging as log
import uuid
import datetime as dt
from typing import Optional, List

from ismcore.model.base_model import Session, SessionMessage
from ismcore.storage.processor_state_storage import SessionStorage

from ismdb.base import BaseDatabaseAccessSinglePool

logging = log.getLogger(__name__)


class SessionDatabaseStorage(SessionStorage, BaseDatabaseAccessSinglePool):

    def create_session(self, user_id: str) -> Optional[Session]:
        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = f"""INSERT INTO session (session_id, created_date, owner_user_id)
                          VALUES (%s, %s, %s)
                              ON CONFLICT (session_id) 
                              DO NOTHING
                """.strip()

                session = Session(
                    session_id=str(uuid.uuid4()),
                    created_date=dt.datetime.utcnow(),
                    owner_user_id=user_id
                )

                cursor.execute(sql, [
                    session.session_id,
                    session.created_date,
                    session.owner_user_id
                ])

                conn.commit()
                return session
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def fetch_session(self, user_id: str , session_id: str) -> Optional[Session]:
        sql = """
            select * from session 
             where (session_id = %s and owner_user_id = %s) 
                or session_id in (select session_id 
                                    from user_session_access 
                                   where session_id = %s and user_id = %s)
        """.strip()

        session = self.execute_query_fixed(
            sql=sql,
            params=[session_id, user_id, session_id, user_id],
            mapper=lambda row: Session(**row)
        )

        if not session:
            return None

        if len(session) == 1:
            return session[0]

        raise ValueError(f'invalid sessions returned for given session: {session_id},  user: {user_id}')

    def fetch_user_sessions(self, user_id: str) -> Optional[List[Session]]:
        sql = """
            select * from session 
             where (owner_user_id = %s) 
                or session_id in (select session_id 
                                    from user_session_access 
                                   where user_id = %s)
        """.strip()

        sessions = self.execute_query_fixed(
            sql=sql,
            params=[user_id, user_id],
            mapper=lambda row: Session(**row)
        )

        return sessions

    def user_join_session(self, user_id: str, session_id: str) -> bool:
        raise NotImplementedError()

    def user_unjoin_session(self, user_id: str, session_id:str) -> bool:
        raise NotImplementedError()

    def fetch_user_session_access(self, user_id: str, session_id: str) -> Optional[Session]:
        session = self.fetch_session(user_id=user_id, session_id=session_id)
        if not session:
            logging.critical(f"attempt access to {session_id} from user {user_id} but no association found")
            return None

        return session

    def insert_session_message(self, message: SessionMessage) -> Optional[SessionMessage]:
        session = self.fetch_user_session_access(user_id=message.user_id, session_id=message.session_id)
        if not session:
            return None

        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = f"""
                    INSERT INTO session_message (session_id, user_id, original_content, executed_content, message_date)
                    VALUES (%s, %s, %s, %s, %s) RETURNING message_id
                """.strip()

                cursor.execute(sql, [
                    message.session_id,
                    message.user_id,
                    message.original_content,
                    message.executed_content,
                    message.message_date
                ])

                message.message_id = cursor.fetchone()[0]

            conn.commit()
            return message
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def fetch_session_messages(self, user_id: str, session_id: str) -> Optional[List[SessionMessage]]:
        if not self.fetch_user_session_access(user_id=user_id, session_id=session_id):
            return None

        return self.execute_query_many(
            sql="SELECT * FROM session_message",
            conditions={
                "session_id": session_id
            }, mapper=lambda row: SessionMessage(**row))

    def delete_session(self, session_id: str) -> int:
        raise NotImplementedError()

