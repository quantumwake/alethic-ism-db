import uuid

from core.processor_state_storage import FieldConfig

from tests import mock_data
from tests.mock_data import (
    db_storage,
)

import datetime as dt


def test_create_session():
    user_profile = mock_data.create_user_profile()
    db_storage.insert_user_profile(user_profile=user_profile)
    #
    # loaded_user_profile = db_storage.user_pr

    session = db_storage.create_session(user_id=user_profile.user_id)

    assert session.session_id is not None
    assert session.created_date is not None
    assert session.created_date.year == dt.datetime.utcnow().year
    assert session.created_date.month == dt.datetime.utcnow().month
    assert session.created_date.day == dt.datetime.utcnow().day

    loaded_session = db_storage.fetch_session(
        user_id=user_profile.user_id,
        session_id=session.session_id
    )

    assert loaded_session is not None
    assert loaded_session.session_id == session.session_id

    loaded_session_by_user = db_storage.fetch_user_sessions(user_id=user_profile.user_id)
    assert len(loaded_session_by_user) >= 1

    # insert a bunch of random messages
    for i in range(1, 5):
        testJson = str({"role": "user", "content": f"hello world {i}"})
        session_message = db_storage.insert_session_message(
            user_id=user_profile.user_id,
            session_id=session.session_id,
            content=testJson
        )

        assert session_message.session_id == session.session_id

    # reload all the session data
    loaded_messages = db_storage.fetch_session_messages(user_profile.user_id, session_id=session.session_id)
    assert len(loaded_messages) == 4



