import uuid
import logging as log
from typing import Optional, List

from ismcore.model.base_model import ProcessorProvider
from ismcore.storage.processor_state_storage import ProcessorProviderStorage

from ismdb.base import BaseDatabaseAccessSinglePool

logging = log.getLogger(__name__)


class ProcessorProviderDatabaseStorage(ProcessorProviderStorage, BaseDatabaseAccessSinglePool):

    def fetch_processor_provider(self, id: str) -> Optional[ProcessorProvider]:
        return self.execute_query_one(
            sql="select * from processor_provider",
            conditions={"id": id},
            mapper=lambda row: ProcessorProvider(**row)
        )

    def fetch_processor_providers(self,
                                  name: str = None,
                                  version: str = None,
                                  class_name: str = None,
                                  user_id: str = None,
                                  project_id: str = None) -> Optional[List[ProcessorProvider]]:

        return self.execute_query_many(
            sql="SELECT * FROM processor_provider",
            conditions={
                'name': name,
                'version': version,
                'class_name': class_name,
                'user_id': user_id,
                'project_id': project_id
            },
            mapper=lambda row: ProcessorProvider(**row))

    def insert_processor_provider(self, provider: ProcessorProvider) -> ProcessorProvider | None:
        conn = self.create_connection()

        try:
            with conn.cursor() as cursor:
                sql = """
                          MERGE INTO processor_provider AS target
                          USING (SELECT 
                                   %s AS id, 
                                   %s AS name, 
                                   %s AS version, 
                                   %s AS class_name,
                                   %s AS user_id,
                                   %s AS project_id) AS source
                             ON target.id = source.id 
                          WHEN MATCHED THEN 
                              UPDATE SET 
                                name = source.name, 
                                version = source.version,
                                class_name = source.class_name
                          WHEN NOT MATCHED THEN 
                              INSERT (id, name, version, class_name, user_id, project_id)
                              VALUES (
                                   source.id, 
                                   source.name, 
                                   source.version, 
                                   source.class_name,
                                   source.user_id,
                                   source.project_id
                              )
                      """

                provider.id = provider.id if provider.id else str(uuid.uuid4())

                cursor.execute(sql, [
                    provider.id,
                    provider.name,
                    provider.version,
                    provider.class_name,
                    provider.user_id,
                    provider.project_id
                ])

                conn.commit()
                return provider
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def delete_processor_provider(self, user_id: str, provider_id: str, project_id: str = None) -> int:
        conn = self.create_connection()

        if not user_id:
            raise Exception('Illegal operations, user_id is mandatory when deleting providers')

        try:
            with conn.cursor() as cursor:

                # user_id is mandatory, cannot delete system level providers
                sql = """
                    DELETE FROM processor_provider 
                     WHERE id = %s 
                       AND user_id=%s
                """

                if project_id:
                    # delete provider with user_id, project_id and provider_idd
                    sql = f"{sql} AND project_id=%s"
                    cursor.execute(sql, [provider_id, user_id, project_id])
                else:
                    # delete provider only with user_id and provider_id
                    cursor.execute(sql, [provider_id, user_id])

                count = cursor.rowcount  # Get the number of rows deleted
                conn.commit()
                return count  # Return the count of deleted rows
        except Exception as e:
            logging.error(e)
            raise e

        finally:
            self.release_connection(conn)
