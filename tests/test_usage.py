from ismcore.storage.processor_state_storage import FieldConfig

from tests.mock_data import db_storage


def test_fetch_usage_report_minutely():
    ## TODO create mocked usage

    usage = db_storage.fetch_usage_report_minutely(
        # user_id="77c17315-3013-5bb8-8c42-32c28618101f",
        user_id="dc688d73-af47-b1df-a24e-b7dfdb618b54",
        project_id='4cfa8c17-420e-4812-aa6b-544bb3ae49f9',
        resource_id=None,
        resource_type=None,
        year=None,
        month=None,
        day=None,
        hour=23,
        minute=51
    )

    assert len(usage) > 0

def test_fetch_usage_report_daily():
    ## TODO create mocked usage

    usage = db_storage.fetch_usage_report_daily(
        # user_id="77c17315-3013-5bb8-8c42-32c28618101f",
        user_id="dc688d73-af47-b1df-a24e-b7dfdb618b54",
        project_id=None,
        # project_id='4cfa8c17-420e-4812-aa6b-544bb3ae49f9',
        resource_id=None,
        resource_type=None,
        year=None,
        month=None,
        day=None
    )

    assert len(usage) > 0

def test_fetch_usage_report():
    """
    Test the flexible fetch_usage_report with various field configurations.
    This demonstrates grouping by dimensions and aggregating metrics.
    """
    usage = db_storage.fetch_usage_report(
        user_id=FieldConfig("user_id", value="dc688d73-af47-b1df-a24e-b7dfdb618b54", use_in_group_by=True, use_in_where=True),
        year=FieldConfig("year", value=None, use_in_group_by=True, use_in_where=False),
        input_count=FieldConfig("input_count", value=None, aggregate="SUM"),
    )

    assert len(usage) == 2

def test_fetch_usage_report_with_multiple_aggregates():
    """
    Test with multiple aggregate functions (SUM, MAX, etc.) on different fields.
    """
    usage = db_storage.fetch_usage_report(
        user_id=FieldConfig("user_id", value="dc688d73-af47-b1df-a24e-b7dfdb618b54", use_in_group_by=True, use_in_where=True),
        resource_type=FieldConfig("resource_type", value=None, use_in_group_by=True, use_in_where=False),
        year=FieldConfig("year", value=None, use_in_group_by=True, use_in_where=False),
        month=FieldConfig("month", value=None, use_in_group_by=True, use_in_where=False),
        input_count=FieldConfig("input_count", value=None, aggregate="SUM"),
        input_tokens=FieldConfig("input_tokens", value=None, aggregate="SUM"),
        output_count=FieldConfig("output_count", value=None, aggregate="SUM"),
        output_tokens=FieldConfig("output_tokens", value=None, aggregate="SUM"),
        total_tokens=FieldConfig("total_tokens", value=None, aggregate="SUM"),
        total_cost=FieldConfig("total_cost", value=None, aggregate="SUM"),
        input_price=FieldConfig("input_price", value=None, aggregate="MAX"),
    )

    assert usage is not None

def test_fetch_user_project_usage_report():
    report = db_storage.fetch_user_project_current_usage_report(
        user_id="dc688d73-af47-b1df-a24e-b7dfdb618b54",
    )

    assert report is not None

def test_fetch_usage_report_total_grouping():
    """
    Test grouping by day-level dimensions to aggregate daily usage.
    """
    usage = db_storage.fetch_usage_report(
        user_id=FieldConfig("user_id", value="dc688d73-af47-b1df-a24e-b7dfdb618b54", use_in_group_by=True, use_in_where=True),
        # year=FieldConfig("year", value=None, use_in_group_by=True, use_in_where=False),
        input_count=FieldConfig("input_count", value=None, aggregate="SUM"),
        input_cost=FieldConfig("input_cost", value=None, aggregate="SUM"),
        input_tokens=FieldConfig("input_tokens", value=None, aggregate="SUM"),
        input_price=FieldConfig("input_price", value=None, aggregate="MAX"),

        output_count=FieldConfig("output_count", value=None, aggregate="SUM"),
        output_cost=FieldConfig("output_cost", value=None, aggregate="SUM"),
        output_tokens=FieldConfig("output_tokens", value=None, aggregate="SUM"),
        output_price=FieldConfig("output_price", value=None, aggregate="MAX"),

        total_tokens=FieldConfig("total_tokens", value=None, aggregate="SUM"),
        total_cost=FieldConfig("total_cost", value=None, aggregate="SUM"),
    )

    assert usage is not None



