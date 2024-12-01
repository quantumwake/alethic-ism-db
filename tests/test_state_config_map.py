from core.vault.vault_model import ConfigMap, ConfigMapType

from alethic_ism_db.db.processor_state_db_storage import ConfigMapDatabaseStorage
from tests.mock_data import DATABASE_URL

config_map_storage = ConfigMapDatabaseStorage(database_url=DATABASE_URL)


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

    print(config)

