import uuid
import logging as log
from typing import Optional

from ismcore.storage.processor_state_storage import ConfigMapStorage
from ismcore.vault.vault_model import ConfigMap
from psycopg2._json import Json     # TODO this is a psycopg2 specific import, we should not be using this here

from ismdb.base import BaseDatabaseAccessSinglePool

logging = log.getLogger(__name__)


class ConfigMapDatabaseStorage(ConfigMapStorage, BaseDatabaseAccessSinglePool):
    def fetch_config_map(self, config_id: str) -> Optional[ConfigMap]:
        return self.execute_query_one(
            sql="SELECT * FROM config_map",
            conditions={'id': config_id},
            mapper=lambda row: ConfigMap(**row)
        )

    def insert_config_map(self, config: ConfigMap) -> Optional[ConfigMap]:
        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = f"""
                    INSERT INTO config_map (
                        id,
                        name,
                        type,
                        data,
                        vault_key_id,
                        vault_id,
                        owner_id,
                        created_at)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, current_timestamp)
                             ON CONFLICT (id)
                      DO UPDATE SET
                           updated_at = current_timestamp,
                           name = EXCLUDED.name,
                           data = EXCLUDED.data,
                           type = EXCLUDED.type,
                           vault_id = EXCLUDED.vault_id,
                           owner_id = EXCLUDED.owner_id
                """

                if not config.id:
                    config.id = str(uuid.uuid4())

                cursor.execute(sql, [
                    config.id,
                    config.name,
                    config.type.value,
                    Json(config.data),
                    config.vault_key_id,
                    config.vault_id,
                    config.owner_id
                ])

                conn.commit()
            return config
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def delete_config_map(self, config_id: str) -> int:
        return self.execute_delete_query("DELETE FROM config_map", conditions={'id': config_id})
