import logging as log
import uuid
from typing import Optional, List

from ismcore.storage.processor_state_storage import VaultStorage
from ismcore.vault.vault_model import Vault
from psycopg2._json import Json

from ismdb.base import BaseDatabaseAccessSinglePool

logging = log.getLogger(__name__)


class VaultDatabaseStorage(VaultStorage, BaseDatabaseAccessSinglePool):
    def fetch_vault(self, vault_id: str) -> Optional[Vault]:
        return self.execute_query_one(
            sql="SELECT * FROM vault",
            conditions={'id': vault_id},
            mapper=lambda row: Vault(**row)
        )

    def fetch_vaults_by_owner(self, owner_id: str) -> Optional[List[Vault]]:
        return self.execute_query_many(
            sql="SELECT * FROM vault",
            conditions={'owner_id': owner_id},
            mapper=lambda row: Vault(**row)
        )

    def insert_vault(self, vault: Vault) -> Optional[Vault]:
        try:
            self.execute_update()
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = f"""
                         INSERT INTO vault (
                             id,
                             name,
                             type,
                             metadata,
                             owner_id,
                             created_at)
                              VALUES (%s, %s, %s, %s, %s, current_timestamp)
                                  ON CONFLICT (id)
                           DO UPDATE SET
                                updated_at = current_timestamp,
                                name = EXCLUDED.name,
                                metadata = EXCLUDED.metadata,
                                type = EXCLUDED.type,
                                owner_id = EXCLUDED.owner_id
                     """

                if not vault.id:
                    vault.id = str(uuid.uuid4())

                cursor.execute(sql, [
                    vault.id,
                    vault.name,
                    vault.type.value,
                    Json(vault.metadata),
                    vault.owner,
                ])

                conn.commit()
            return vault
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def delete_vault(self, vault_id: str) -> int:
        return self.execute_delete_query(
            sql="delete from vault",
            conditions={'id': vault_id}
        )
