from ismcore.storage.processor_state_storage import FieldConfig

from tests.mock_data import db_storage


def test_fetch_usage_report():
    ## TODO create mocked usage

    usage = db_storage.fetch_usage_report(
        user_id=FieldConfig("user_id", value="77c17315-3013-5bb8-8c42-32c28618101f", use_in_group_by=True, use_in_where=True),
        resource_type=FieldConfig("resource_type", value=None, use_in_group_by=True, use_in_where=False),
        year=FieldConfig("year", value=None, use_in_group_by=True, use_in_where=False),
        unit_type=FieldConfig("unit_type", value=None, use_in_group_by=True, use_in_where=False)
    )

    assert len(usage) == 2
    # assert projects[0].project_name == project1.project_name
    # assert projects[1].project_name == project2.project_name



