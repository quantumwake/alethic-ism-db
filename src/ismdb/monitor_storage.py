import logging as log
import datetime as dt
from typing import Optional, List

from ismcore.model.base_model import MonitorLogEvent
from ismcore.storage.processor_state_storage import MonitorLogEventStorage

from .base import BaseDatabaseAccessSinglePool

logging = log.getLogger(__name__)


class MonitorLogEventDatabaseStorage(MonitorLogEventStorage, BaseDatabaseAccessSinglePool):

    # def fetch_monitor_log_events(
    #         self,
    #         internal_reference_id: int = None,
    #         user_id: str = None,
    #         project_id: str = None) -> Optional[List[MonitorLogEvent]]:

    def fetch_monitor_log_events(self,
                                 user_id: str = None,
                                 project_id: str = None,
                                 reference_id: str = None,
                                 start_date: dt.datetime = None,
                                 end_date: dt.datetime = None,
                                 order_by: [str] = None) -> Optional[List[MonitorLogEvent]]:

        if not user_id and not project_id and not reference_id:
            raise ValueError(f'at least one search criteria must be defined, '
                             f'internal_reference_id, user_id or project_id')

        if not start_date:
            start_date = dt.datetime.now() - dt.timedelta(days=7)

        if dt.datetime.now() - start_date > dt.timedelta(days=14):
            raise ValueError(f'start date must be within 14 days of the current date')

        if not end_date:
            end_date = dt.datetime.now()

        if not order_by:
            order_by = ["log_id desc"]

        return self.execute_query_many2(
            sql="select * from monitor_log_event",
            conditions={
                'internal_reference_id': reference_id,
                'user_id': user_id,
                'project_id': project_id,
                'log_time': (start_date, end_date)
            },
            mapper=lambda row: MonitorLogEvent(**row),
            order_by=order_by
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

    def insert_monitor_log_event(self, monitor_log_event: MonitorLogEvent) -> Optional[MonitorLogEvent]:

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
