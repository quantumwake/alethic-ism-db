from typing import List

from ismcore.model.base_model import UsageReport
from ismcore.storage.processor_state_storage import UsageStorage, FieldConfig
from ismdb.base import BaseDatabaseAccessSinglePool


class UsageDatabaseStorage(UsageStorage, BaseDatabaseAccessSinglePool):

    def fetch_usage_report_minutely(self, user_id, project_id, resource_id, resource_type, year, month, day, hour, minute) -> List[UsageReport]:
        base_sql = "SELECT * FROM USAGE_MINUTELY_V"

        conditions = {
            "user_id": user_id,
            "project_id": project_id,
            "resource_id": resource_id,
            "resource_type": resource_type,
            "year": year,
            "month": month,
            "day": day,
            "hour": hour,
            "minute": minute,
        }

        return self.execute_query_many(base_sql, conditions, lambda row: UsageReport(**row))

    def fetch_usage_report_hourly(self, user_id, project_id, resource_id, resource_type, year, month, day, hour) -> List[UsageReport]:
        base_sql = "SELECT * FROM USAGE_HOURLY_V"

        conditions = {
            "user_id": user_id,
            "project_id": project_id,
            "resource_id": resource_id,
            "resource_type": resource_type,
            "year": year,
            "month": month,
            "day": day,
            "hour": hour,
        }

        return self.execute_query_many(base_sql, conditions, lambda row: UsageReport(**row))

    def fetch_usage_report_daily(self, user_id, project_id, resource_id, resource_type, year, month, day) -> List[UsageReport]:
        base_sql = "SELECT * FROM USAGE_DAILY_V"

        conditions = {
            "user_id": user_id,
            "project_id": project_id,
            "resource_id": resource_id,
            "resource_type": resource_type,
            "year": year,
            "month": month,
            "day": day
        }

        return self.execute_query_many(base_sql, conditions, lambda row: UsageReport(**row))

    def fetch_usage_report_monthly(self, user_id, project_id, resource_id, resource_type, year, month) -> List[UsageReport]:
        base_sql = "SELECT * FROM USAGE_MONTHLY_V"

        conditions = {
            "user_id": user_id,
            "project_id": project_id,
            "resource_id": resource_id,
            "resource_type": resource_type,
            "year": year,
            "month": month,
        }

        return self.execute_query_many(base_sql, conditions, lambda row: UsageReport(**row))


    def fetch_usage_report_yearly(self, user_id, project_id, resource_id, resource_type, year) -> List[UsageReport]:
        base_sql = "SELECT * FROM USAGE_YEARLY_V"

        conditions = {
            "user_id": user_id,
            "project_id": project_id,
            "resource_id": resource_id,
            "resource_type": resource_type,
            "year": year,
        }

        return self.execute_query_many(base_sql, conditions, lambda row: UsageReport(**row))

    def fetch_usage_report(self, **kwargs) -> List[UsageReport]:
        """
        Flexible usage report fetcher that accepts any number of FieldConfig parameters.

        Example usage:
            usage = db_storage.fetch_usage_report(
                user_id=FieldConfig("user_id", value="...", use_in_group_by=True, use_in_where=True),
                year=FieldConfig("year", value=None, use_in_group_by=True, use_in_where=False),
                input_count=FieldConfig("input_count", value=None, aggregate="SUM"),
                input_cost=FieldConfig("input_cost", value=None, aggregate="SUM"),
                total_cost=FieldConfig("total_cost", value=None, aggregate="MAX"),
            )

        :param kwargs: Any number of FieldConfig objects keyed by their parameter names
        :return: List of UsageReport objects
        """
        base_sql = "FROM usage_minutely_v"

        # Extract FieldConfig objects from kwargs and filter out None values
        conditions_and_grouping = [field_config for field_config in kwargs.values()
                                   if field_config is not None and isinstance(field_config, FieldConfig)]

        if not conditions_and_grouping:
            raise ValueError("At least one FieldConfig must be provided")

        # Execute the query with dynamic conditions and grouping
        return self.execute_query_grouped(base_sql, conditions_and_grouping, lambda row: UsageReport(**row))

    #
    # def fetch_usage_report(
    #         self,
    #         user_id: FieldConfig,
    #         project_id: Optional[FieldConfig] = None,
    #         resource_id: Optional[FieldConfig] = None,
    #         resource_type: Optional[FieldConfig] = None,
    #         year: Optional[FieldConfig] = None,
    #         month: Optional[FieldConfig] = None,
    #         day: Optional[FieldConfig] = None,
    #         unit_type: Optional[FieldConfig] = None,
    #         unit_subtype: Optional[FieldConfig] = None
    # ) -> List[UsageReport]:
    #     # base_sql = "FROM usage_v u INNER JOIN user_project up ON up.project_id = u.project_id"
    #     base_sql = "FROM usage_v"
    #
    #     # List of FieldConfig objects
    #     conditions_and_grouping = [
    #         user_id,
    #         project_id if project_id else None,
    #         resource_id if resource_id else None,
    #         resource_type if resource_type else None,
    #         year if year else None,
    #         month if month else None,
    #         day if day else None,
    #         unit_type if unit_type else None,
    #         unit_subtype if unit_subtype else None
    #     ]
    #
    #     # Remove None entries (for optional fields that were not provided)
    #     conditions_and_grouping = [entry for entry in conditions_and_grouping if entry is not None]
    #
    #     # Execute the query with dynamic conditions and grouping
    #     return self.execute_query_grouped(base_sql, conditions_and_grouping, lambda row: UsageReport(**row))
