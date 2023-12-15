import os
import random
# import pytest

from core.processor_state import State, StateConfigLM

from alethic_ism_db.db.processor_state_db import ProcessorStateDatabaseStorage

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres1@localhost:5432/postgres")


def create_mock_state() -> State:
    state = State(
        config=StateConfigLM(
            name="Test Me",
            version="Test version 1.0",
            model_name="Hello World Model",
            provider_name="Hello World Provider",
            user_template_path="./test_templates/test_template_P1_user.json",
            system_template_path="./test_templates/test_template_P1_system.json"
        )
    )

    for i in range(5):

        for j in range(5):
            query_state = {
                "state_key": f"hello_world_state_key_{i}",
                "data": random.randbytes(64),
                "index": (j+1)*(i+1)
            }

            state.apply_columns(query_state=query_state)
            state.apply_row_data(query_state=query_state)

    return state


def test_state_persistence():
    state = create_mock_state()

    assert state != None

    db_storage = ProcessorStateDatabaseStorage(database_url=DATABASE_URL)
    db_storage.save_state(state=state)


