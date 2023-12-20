from gdrive.pivot.builder import PivotTableBuilder
from gdrive.pivot.enums import (
    FilterTypeEnum,
    SortOrderEnum,
    SummarizeFunctionEnum,
    ValueLayoutEnum,
)
from gdrive.pivot.scaffold import UserEnteredValueScaffold


class IDVAPivotDirector:
    def event_by_source_counter(
        self, col_dict: dict, event: str, source: str
    ) -> object:
        builder = PivotTableBuilder(0, col_dict)

        builder.add_row("eventName", sortOrder=SortOrderEnum.ASCENDING)
        builder.add_row("firstUserSource", sortOrder=SortOrderEnum.ASCENDING)
        builder.add_row("eventCount", sortOrder=SortOrderEnum.ASCENDING)

        builder.add_filter(
            "eventName",
            filter_type=FilterTypeEnum.TEXT_CONTAINS,
            values=[UserEnteredValueScaffold(event)],
        )

        builder.add_filter(
            "firstUserSource",
            filter_type=FilterTypeEnum.TEXT_CONTAINS,
            values=[UserEnteredValueScaffold(source)],
        )

        builder.add_value("eventCount", SummarizeFunctionEnum.SUM)
        builder.set_value_layout(ValueLayoutEnum.HORIZONTAL)
        return builder.as_dict()

    def event_by_medium_counter(
        self, col_dict: dict, event: str, source: str
    ) -> object:
        builder = PivotTableBuilder(0, col_dict)

        builder.add_row("eventName", sortOrder=SortOrderEnum.ASCENDING)
        builder.add_row("firstUserMedium", sortOrder=SortOrderEnum.ASCENDING)
        builder.add_row("eventCount", sortOrder=SortOrderEnum.ASCENDING)

        builder.add_filter(
            "eventName",
            filter_type=FilterTypeEnum.TEXT_CONTAINS,
            values=[UserEnteredValueScaffold(event)],
        )

        builder.add_filter(
            "firstUserMedium",
            filter_type=FilterTypeEnum.TEXT_CONTAINS,
            values=[UserEnteredValueScaffold(source)],
        )

        builder.add_value("eventCount", SummarizeFunctionEnum.SUM)
        builder.set_value_layout(ValueLayoutEnum.HORIZONTAL)
        return builder.as_dict()

    def feedback(self, col_dict: dict) -> str:
        builder = PivotTableBuilder(0, col_dict)
        builder.add_row("eventName", sortOrder=SortOrderEnum.ASCENDING)
        builder.add_row("eventCount", sortOrder=SortOrderEnum.ASCENDING)
        builder.add_filter(
            "linkUrl",
            filter_type=FilterTypeEnum.TEXT_CONTAINS,
            values=[UserEnteredValueScaffold("feedback")],
        )
        builder.add_value("eventCount", SummarizeFunctionEnum.SUM)
        builder.set_value_layout(ValueLayoutEnum.HORIZONTAL)
        return builder.as_dict()

    def clicks(self, col_dict: dict) -> str:
        builder = PivotTableBuilder(0, col_dict)
        builder.add_row("eventName", sortOrder=SortOrderEnum.ASCENDING)
        builder.add_row("eventCount", sortOrder=SortOrderEnum.ASCENDING)
        builder.add_value("eventCount", SummarizeFunctionEnum.SUM)
        return builder.as_dict()
