import re
from typing import List, Type, cast, T

from ismcore.model.base_model_usage_and_limits import (UsageReport, UserProjectCurrentUsageReport)
from ismcore.storage.processor_state_storage import UsageStorage, FieldConfig
from pydantic import BaseModel

from ismdb.base import BaseDatabaseAccessSinglePool

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_$.]*$")

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

    def fetch_usage_report_generic(
            self,
            table_or_view: str = "usage_minutely_v",
            model: Type[T] = cast(Type[T], UsageReport),  # default, but still generic
            **kwargs
    ) -> List[T]:
        """
        Flexible usage report fetcher that accepts any number of FieldConfig parameters.
        Works for any table/view and any Pydantic model.

        :param table_or_view: table or view name to select FROM
        :param model: Pydantic model class to materialize rows into (generic T)
        :param kwargs: Any number of FieldConfig objects keyed by their parameter names
        :return: List[T]
        """
        if not _IDENTIFIER_RE.match(table_or_view):
            raise ValueError(f"Invalid table/view name: {table_or_view}")

        base_sql = f"FROM {table_or_view}"

        conditions_and_grouping = [
            fc for fc in kwargs.values()
            if fc is not None and isinstance(fc, FieldConfig)
        ]
        if not conditions_and_grouping:
            raise ValueError("At least one FieldConfig must be provided")

        return self.execute_query_grouped(
            base_sql,
            conditions_and_grouping,
            lambda row: model(**row)  # -> T
        )

    def fetch_user_project_current_usage_report(self, user_id: str,
                                                project_id: str = None) -> UserProjectCurrentUsageReport | None:
        kwargs = {
            "table_or_view": "user_project_current_usage_report",
            "model": UserProjectCurrentUsageReport,
            "user_id": FieldConfig("user_id", value=user_id, use_in_group_by=True, use_in_where=True),
            "tier_id": FieldConfig("tier_id", value=None, use_in_group_by=True, use_in_where=False),

            ### tier / quota token limits for a period
            "limit_per_minute": FieldConfig("limit_token_per_minute", value=None, use_in_where=False, aggregate="MAX"),
            "limit_per_hour": FieldConfig("limit_token_per_hour", value=None, use_in_where=False, aggregate="MAX"),
            "limit_per_day": FieldConfig("limit_token_per_day", value=None, use_in_where=False, aggregate="MAX"),
            "limit_per_month": FieldConfig("limit_token_per_month", value=None, use_in_where=False, aggregate="MAX"),
            "limit_per_year": FieldConfig("limit_token_per_year", value=None, use_in_where=False, aggregate="MAX"),

            ### tier / quotas cost limits for a period
            "limit_cost_per_minute": FieldConfig("limit_cost_per_minute", value=None, use_in_where=True,
                                                 aggregate="MAX"),
            "limit_cost_per_hour": FieldConfig("limit_cost_per_hour", value=None, use_in_where=True, aggregate="MAX"),
            "limit_cost_per_day": FieldConfig("limit_cost_per_day", value=None, use_in_where=True, aggregate="MAX"),
            "limit_cost_per_month": FieldConfig("limit_cost_per_month", value=None, use_in_where=True, aggregate="MAX"),
            "limit_cost_per_year": FieldConfig("limit_cost_per_year", value=None, use_in_where=True, aggregate="MAX"),

            # current running costs
            "cur_minute_total_cost": FieldConfig("cur_minute_total_cost", value=None, use_in_where=True,
                                                 aggregate="SUM"),
            "cur_hour_total_cost": FieldConfig("cur_hour_total_cost", value=None, use_in_where=True, aggregate="SUM"),
            "cur_day_total_cost": FieldConfig("cur_day_total_cost", value=None, use_in_where=True, aggregate="SUM"),
            "cur_month_total_cost": FieldConfig("cur_month_total_cost", value=None, use_in_where=True, aggregate="SUM"),
            "cur_year_total_cost": FieldConfig("cur_year_total_cost", value=None, use_in_where=True, aggregate="SUM"),

            ##
            "pct_minute_tokens_used": FieldConfig("pct_minute_tokens_used", value=None, aggregate="SUM"),
            "pct_hour_tokens_used": FieldConfig("pct_hour_tokens_used", value=None, aggregate="SUM"),
            "pct_day_tokens_used": FieldConfig("pct_day_tokens_used", value=None, aggregate="SUM"),
            "pct_month_tokens_used": FieldConfig("pct_month_tokens_used", value=None, aggregate="SUM"),
            "pct_year_tokens_used": FieldConfig("pct_year_tokens_used", value=None, aggregate="SUM"),
            "pct_minute_cost_used": FieldConfig("pct_minute_cost_used", value=None, aggregate="SUM"),
            "pct_hour_cost_used": FieldConfig("pct_hour_cost_used", value=None, aggregate="SUM"),
            "pct_day_cost_used": FieldConfig("pct_day_cost_used", value=None, aggregate="SUM"),
            "pct_month_cost_used": FieldConfig("pct_month_cost_used", value=None, aggregate="SUM"),
            "pct_year_cost_used": FieldConfig("pct_year_cost_used", value=None, aggregate="SUM"),
        }

        if project_id is not None:
            kwargs["project_id"] = FieldConfig("project_id", value=project_id, use_in_group_by=True, use_in_where=True)

        report = self.fetch_usage_report_generic(**kwargs)

        if len(report) == 0:
            return None

        if len(report) == 1:
            return report[0]

        raise ValueError(
            f"Expected 0 or 1 usage reports for user_id {user_id}, got {len(report)}, which is unexpected.")

    # def fetch_user_usage_summary(self, user_id: str) -> List[UsageReport]:
    #     """
    #     Test grouping by day-level dimensions to aggregate daily usage.
    #     """
    #     usage = db_storage.fetch_usage_report(
    #         user_id=FieldConfig("user_id", value="dc688d73-af47-b1df-a24e-b7dfdb618b54", use_in_group_by=True,
    #                             use_in_where=True),
    #         # year=FieldConfig("year", value=None, use_in_group_by=True, use_in_where=False),
    #         input_count=FieldConfig("input_count", value=None, aggregate="SUM"),
    #         input_cost=FieldConfig("input_cost", value=None, aggregate="SUM"),
    #         input_tokens=FieldConfig("input_tokens", value=None, aggregate="SUM"),
    #         input_price=FieldConfig("input_price", value=None, aggregate="MAX"),
    #
    #         output_count=FieldConfig("output_count", value=None, aggregate="SUM"),
    #         output_cost=FieldConfig("output_cost", value=None, aggregate="SUM"),
    #         output_tokens=FieldConfig("output_tokens", value=None, aggregate="SUM"),
    #         output_price=FieldConfig("output_price", value=None, aggregate="MAX"),
    #
    #         total_tokens=FieldConfig("total_tokens", value=None, aggregate="SUM"),
    #         total_cost=FieldConfig("total_cost", value=None, aggregate="SUM"),
    #     )
    #
    #     assert usage is not None
    #
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
