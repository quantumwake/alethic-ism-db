from ismcore.vault.vault_model import Vault, VaultType

from ismdb.configmap_storage import ConfigMapDatabaseStorage
from ismdb.vault_storage import VaultDatabaseStorage
from tests.mock_data import DATABASE_URL

config_map_storage = ConfigMapDatabaseStorage(database_url=DATABASE_URL)
vault_storage = VaultDatabaseStorage(database_url=DATABASE_URL)


def test_create_vault():
    vault = Vault(
        name="test-vault",
        owner="test-owner",
        type=VaultType.LOCAL,
        metadata={"test": "metadata"}
    )

    vault = vault_storage.insert_vault(vault=vault)
    assert vault.id is not None


    # id: str
    # name: str
    # owner: Optional[str] = None
    # # TODO credentials such as api keys or other if we want to support multiple vaults on a per owner basis
    # type: VaultType = VaultType.LOCAL  # e.g., 'kms', 'vault', 'local', other provider
    # metadata: Optional[Json] = None  # Additional metadata in JSON format
    # created_at: Optional[dt.datetime] = None  # ISO timestamp
    # updated_at: Optional[dt.datetime] = None  # ISO timestamp


def test_create_config_map():

    config = ConfigMap(
        name="test-config-map",
        type=ConfigMapType.CONFIG_MAP,
        data={"test": "data"},
        owner_id="aaaaaaaa-aaaa-aaaa-aaaa-test-owner",
        vault_id=None,
        vault_key_id=None,
    )

    config = config_map_storage.insert_config_map(config=config)
    assert config.id is not None

    found_config = config_map_storage.fetch_config_map(config_id=config.id)
    assert found_config.id == config.id
    assert found_config.name == config.name
    assert found_config.type == config.type
    assert found_config.data == config.data
    assert found_config.owner_id == config.owner_id
    assert found_config.vault_id == config.vault_id
    assert found_config.vault_key_id == config.vault_key_id

    found_config.data = {"other_data": "data2", **found_config.data}
    config_map_storage.insert_config_map(config=found_config)
    found_config = config_map_storage.fetch_config_map(config_id=config.id)
    assert found_config.data == {"other_data": "data2", "test": "data"}
