from typing import List, Optional

from ismcore.model.base_model import UsageReport
from ismcore.storage.processor_state_storage import UsageStorage, FieldConfig
from ismdb.base import BaseDatabaseAccessSinglePool


class UsageDatabaseStorage(UsageStorage, BaseDatabaseAccessSinglePool):

    def fetch_usage_report(
            self,
            user_id: FieldConfig,
            project_id: Optional[FieldConfig] = None,
            resource_id: Optional[FieldConfig] = None,
            resource_type: Optional[FieldConfig] = None,
            year: Optional[FieldConfig] = None,
            month: Optional[FieldConfig] = None,
            day: Optional[FieldConfig] = None,
            unit_type: Optional[FieldConfig] = None,
            unit_subtype: Optional[FieldConfig] = None
    ) -> List[UsageReport]:
        # base_sql = "FROM usage_v u INNER JOIN user_project up ON up.project_id = u.project_id"
        base_sql = "FROM usage_v"

        # List of FieldConfig objects
        conditions_and_grouping = [
            user_id,
            project_id if project_id else None,
            resource_id if resource_id else None,
            resource_type if resource_type else None,
            year if year else None,
            month if month else None,
            day if day else None,
            unit_type if unit_type else None,
            unit_subtype if unit_subtype else None
        ]

        # Remove None entries (for optional fields that were not provided)
        conditions_and_grouping = [entry for entry in conditions_and_grouping if entry is not None]

        # Execute the query with dynamic conditions and grouping
        return self.execute_query_grouped(base_sql, conditions_and_grouping, lambda row: UsageReport(**row))
