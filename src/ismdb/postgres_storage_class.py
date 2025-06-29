import logging as log

from ismcore.storage.processor_state_storage import StateMachineStorage

from ismdb.configmap_storage import ConfigMapDatabaseStorage
from ismdb.monitor_storage import MonitorLogEventDatabaseStorage
from ismdb.processor_provider_storage import ProcessorProviderDatabaseStorage
from ismdb.processor_state_storage import ProcessorStateDatabaseStorage
from ismdb.processor_storage import ProcessorDatabaseStorage
from ismdb.session_storage import SessionDatabaseStorage
from ismdb.state_action_storage import StateActionDatabaseStorage
from ismdb.state_storage import StateDatabaseStorage
from ismdb.template_storage import TemplateDatabaseStorage
from ismdb.usage_storage import UsageDatabaseStorage
from ismdb.user_project_storage import UserProjectDatabaseStorage
from ismdb.user_storage import UserProfileDatabaseStorage
from ismdb.vault_storage import VaultDatabaseStorage
from ismdb.workflow_storage import WorkflowDatabaseStorage
from ismdb.filter import FilterDatabaseStorage

logging = log.getLogger(__name__)


class PostgresDatabaseStorage(StateMachineStorage):

    def __init__(self, database_url: str, incremental: bool = True, *args, **kwargs):
        super().__init__(
            state_storage=StateDatabaseStorage(database_url=database_url, incremental=incremental),
            processor_storage=ProcessorDatabaseStorage(database_url=database_url, incremental=incremental),
            processor_state_storage=ProcessorStateDatabaseStorage(database_url=database_url, incremental=incremental),
            processor_provider_storage=ProcessorProviderDatabaseStorage(database_url=database_url, incremental=incremental),
            workflow_storage=WorkflowDatabaseStorage(database_url=database_url, incremental=incremental),
            template_storage=TemplateDatabaseStorage(database_url=database_url, incremental=incremental),
            user_profile_storage=UserProfileDatabaseStorage(database_url=database_url, incremental=incremental),
            user_project_storage=UserProjectDatabaseStorage(database_url=database_url, incremental=incremental),
            monitor_log_event_storage=MonitorLogEventDatabaseStorage(database_url=database_url, incremental=incremental),
            usage_storage=UsageDatabaseStorage(database_url=database_url, incremental=incremental),
            session_storage=SessionDatabaseStorage(database_url=database_url, incremental=incremental),
            state_action_storage=StateActionDatabaseStorage(database_url=database_url, incremental=incremental),
            vault_storage=VaultDatabaseStorage(database_url=database_url, incremental=incremental),
            config_map_storage=ConfigMapDatabaseStorage(database_url=database_url, incremental=incremental),
            filter_storage=FilterDatabaseStorage(database_url=database_url, incremental=incremental),
        )

#
# class PostgresDatabaseWithRedisCacheStorage(PostgresDatabaseStorage):
#     def __init__(self, database_url: str, incremental: bool = True, *args, **kwargs):
#         super().__init__(database_url=database_url, incremental=incremental, **kwargs)
#         # the storage system for sessions is redis
#         self._delegate_session_storage = RedisSessionStorage(
#             host=os.environ.get("REDIS_HOST", "localhost"),
#             port=os.environ.get("REDIS_PORT", 6379),
#             password=os.environ.get("REDIS_PASS", None)
#         )
