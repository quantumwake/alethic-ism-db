import logging as log

from typing import Optional, List
from core.base_model import MonitorLogEvent
from core.processor_state_storage import MonitorLogEventStorage
from .base import BaseDatabaseAccessSinglePool

logging = log.getLogger(__name__)


class MonitorLogEventDatabaseStorage(MonitorLogEventStorage, BaseDatabaseAccessSinglePool):

    def fetch_monitor_log_events(
            self,
            internal_reference_id: int = None,
            user_id: str = None,
            project_id: str = None) -> Optional[List[MonitorLogEvent]]:

        if not internal_reference_id and not user_id and not project_id:
            raise ValueError(f'at least one search criteria must be defined, '
                             f'internal_reference_id, user_id or project_id')

        return self.execute_query_many(
            sql="select * from monitor_log_event",
            conditions={
                'internal_reference_id': internal_reference_id,
                'user_id': user_id,
                'project_id': project_id
            },
            mapper=lambda row: MonitorLogEvent(**row)
        )

    def delete_monitor_log_event(
            self,
            log_id: str = None,
            user_id: str = None,
            project_id: str = None,
            force: bool = False) -> int:

        # at-least one parameter must be defined (or forced)
        if not (id or user_id or project_id) and not force:
            return 0

        # delete the monitor log based on input parameters
        return self.execute_delete_query(
            "delete from monitor_log_event",
            conditions={
                "log_id": log_id,
                "user_id": user_id,
                "project_id": project_id
            }
        )

    def insert_monitor_log_event(self, monitor_log_event: MonitorLogEvent) -> MonitorLogEvent:

        try:
            conn = self.create_connection()
            with (conn.cursor() as cursor):
                sql = """
                    INSERT INTO monitor_log_event (
                        log_type,
                        internal_reference_id,
                        user_id,
                        project_id,
                        exception,
                        data
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING log_id, log_time 
                """

                cursor.execute(sql, [
                    monitor_log_event.log_type,
                    monitor_log_event.internal_reference_id,
                    monitor_log_event.user_id,
                    monitor_log_event.project_id,
                    monitor_log_event.exception,
                    monitor_log_event.data
                ])

                # fetch the id from the returning sql statement
                returned = cursor.fetchone()
                monitor_log_event.log_id = returned[0]  # serial id / sequence
                monitor_log_event.log_time = returned[1]  # log time

            conn.commit()
            return monitor_log_event
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)
