import uuid
import logging as log
from typing import Optional, List

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

        for p in processors:
            p.properties = self.fetch_processor_properties(processor_id=p.id)

        return processors

    def fetch_processor(self, processor_id: str) -> Optional[Processor]:
        processor = self.execute_query_one(
            sql="SELECT * FROM processor",
            conditions={
                'id': processor_id
            },
            mapper=lambda row: Processor(**row))

        if processor:
            processor.properties = self.fetch_processor_properties(processor_id=processor_id)

        return processor

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

    def insert_processor(self, processor: Processor) -> Processor:
        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = f"""
                    INSERT INTO processor (id, provider_id, project_id, status)
                         VALUES (%s, %s, %s, %s)
                             ON CONFLICT (id) 
                      DO UPDATE SET 
                        provider_id = EXCLUDED.provider_id
--                         status = EXCLUDED.status
                """

                processor.id = processor.id if processor.id else str(uuid.uuid4())

                cursor.execute(sql, [
                    processor.id,
                    processor.provider_id,
                    processor.project_id,
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

    def fetch_processor_properties(self, processor_id: str, name: str = None) -> Optional[List[ProcessorProperty]]:
        return self.execute_query_many(
            sql="SELECT * FROM processor_property",
            conditions={
                'processor_id': processor_id,
                'name': name
            },
            mapper=lambda row: ProcessorProperty(**row))
    #c
    # def fetch_processor_property_by_name(self, processor_id: str, property_name: str):
    #     return self.execute_query_one(
    #         sql="SELECT * FROM processor_property",
    #         conditions={
    #             'processor_id': processor_id,
    #             'name': property_name
    #         },
    #         mapper=lambda row: ProcessorProperty(**row)
    #     )
    #
    # def update_processor_property(self, processor_id: str, property_name: str, property_value: str) -> int:
    #     return self.execute_update(
    #         table="processor_property",
    #         update_values={
    #             "value": property_value
    #         },
    #         conditions={
    #             'processor_id': processor_id,
    #             'name': property_name
    #         },
    #     )
    #
    # def insert_processor_properties(self, properties: List[ProcessorProperty]) -> List[ProcessorProperty]:
    #     try:
    #         conn = self.create_connection()
    #         with conn.cursor() as cursor:
    #             sql = f"""
    #                 INSERT INTO processor_property (processor_id, name, value)
    #                      VALUES (%s, %s, %s)
    #                          ON CONFLICT (processor_id, name)
    #                   DO UPDATE SET
    #                        value = EXCLUDED.value
    #             """
    #
    #             for property in properties:
    #                 cursor.execute(sql, [
    #                     property.processor_id,
    #                     property.name,
    #                     property.value
    #                 ])
    #
    #             conn.commit()
    #         return properties
    #     except Exception as e:
    #         logging.error(e)
    #         raise e
    #     finally:
    #         self.release_connection(conn)
    #
    # def delete_processor_property(self, processor_id: str, name: str) -> int:
    #     return self.execute_delete_query(
    #         sql="DELETE FROM processor_property",
    #         conditions={
    #             'processor_id': processor_id,
    #             'name': name
    #         }
    #     )
