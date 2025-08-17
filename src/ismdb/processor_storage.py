import uuid
import logging as log
from typing import Optional, List

from psycopg2.extras import Json
from ismcore.model.base_model import Processor, ProcessorStatusCode, ProcessorProperty
from ismcore.storage.processor_state_storage import ProcessorStorage

from ismdb.base import BaseDatabaseAccessSinglePool

logging = log.getLogger(__name__)


class ProcessorDatabaseStorage(ProcessorStorage, BaseDatabaseAccessSinglePool):
    def fetch_processors(self, provider_id: str = None, project_id: str = None) -> List[Processor]:
        processors = self.execute_query_many(
            sql="SELECT * FROM processor",
            conditions={
                'project_id': project_id,
                'provider_id': provider_id
            },
            mapper=lambda row: Processor(**row))

        if not processors:
            return []

        return processors

    def fetch_processor(self, processor_id: str) -> Optional[Processor]:
        return self.execute_query_one(
            sql="SELECT * FROM processor",
            conditions={'id': processor_id},
            mapper=lambda row: Processor(**row))

    def change_processor_status(self, processor_id: str, status: ProcessorStatusCode) -> int:
        if not processor_id:
            raise ValueError(f'processor id cannot be empty or null')

        return self.execute_update(
            table="processor",
            update_values={
                "status": status.value
            },
            conditions={
                "id": processor_id
            }
        )

    def insert_processor(self, processor: Processor) -> Processor | None:
        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = f"""
                    INSERT INTO processor (id, provider_id, project_id, name, properties, status)
                         VALUES (%s, %s, %s, %s, %s, %s)
                             ON CONFLICT (id) 
                      DO UPDATE SET 
                        provider_id = EXCLUDED.provider_id,
                        properties = EXCLUDED.properties,
                        name = EXCLUDED.name
                """

                processor.id = processor.id if processor.id else str(uuid.uuid4())

                cursor.execute(sql, [
                    processor.id,
                    processor.provider_id,
                    processor.project_id,
                    processor.name,
                    Json(processor.properties) if processor.properties else None,
                    processor.status.value
                ])

                conn.commit()
            return processor
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def delete_processor(self, processor_id: str) -> int:
        return self.execute_delete_query(
            sql="DELETE FROM processor",
            conditions={
                'id': processor_id
            }
        )
