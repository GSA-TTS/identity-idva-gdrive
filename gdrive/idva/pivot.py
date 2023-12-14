from enum import Enum
from abc import ABC, abstractmethod


class FilterTypeEnum(str, Enum):
    TEXT_CONTAINS = "TEXT_CONTAINS"
    TEXT_EQUALS = "TEXT_EQ"


class SortOderEnum(str, Enum):
    ASCENDING = "ASCENDING"
    DESCENDING = "DESCENDING"


class SummarizeFunctionEnum(str, Enum):
    SUM = "SUM"


class ValueLayoutEnum(str, Enum):
    HORIZONTAL = "HORIZONTAL"


class AbstractScaffold(ABC):
    """
    Client code may use classes like UserEnteredValue to add scaffolds to filter criterion builder.
    This supports cases where filter criterion may have large numbers of acceptable scaffolds
    that may be arbitrarily combined. We use AbstractScaffold to ensure type safety in the abritary lists
    """

    @abstractmethod
    def get_scaffold(self):
        pass


class UserEnteredValueScaffold(AbstractScaffold):
    def __init__(self, value: str):
        super.__init__(self)
        self.__scaffold = {"userEnteredValue": value}

    def get_scaffold(self):
        return self.__scaffold


class PivotTableBuilder:
    def __init__(self, source_sheet_id: int = 0) -> None:
        self.source_sheet_id = source_sheet_id
        self.__pivot_scaffold = {
            "pivotTable": {
                "source": {
                    # First Sheet (Sheet1) is always ID 0
                    "sheetId": source_sheet_id,
                },
            }
        }

    def __get_pivot_value(self, field: str) -> dict or None:
        return self.__pivot_scaffold["pivotTable"][field]

    def __set_pivot_value(self, field: str, value: any) -> None:
        self.__pivot_scaffold["pivotTable"][field] = value

    def add_row(
        self,
        source_col_offset: str,
        show_totals: bool = True,
        sortOrder: SortOderEnum = SortOderEnum.ASCENDING,
    ) -> None:
        if self.__get_pivot_value("rows") is None:
            self.__set_pivot_value("rows", [])

        self.__get_pivot_value("rows").append(
            {
                "sourceColumnOffset": source_col_offset,
                "showTotals": show_totals,
                "sortOrder": sortOrder.value,
            }
        )

    def add_value(
        self,
        source_col_offset: str,
        summarize_func: SummarizeFunctionEnum = SummarizeFunctionEnum.SUM,
    ) -> None:
        if self.__get_pivot_value("values") is None:
            self.__set_pivot_value("values", [])

        self.__get_pivot_value("values").append(
            {
                "sourceColumnOffset": source_col_offset,
                "summarizeFunction": summarize_func.value,
            }
        )

    def add_filter(
        self,
        source_col_offset: str,
        filter_type: FilterTypeEnum,
        values: [AbstractScaffold],
        visible_by_default: bool = True,
    ) -> None:
        if self.__get_pivot_value("filterSpecs") is None:
            self.__set_pivot_value("filterSpecs", [])

        self.__get_pivot_value("filterSpecs").append(
            {
                "filterCriteria": {
                    "condition": {
                        "type": filter_type.value,
                        "values": [
                            (AbstractScaffold(val)).get_scaffold() for val in values
                        ],
                    },
                    "visibleByDefault": visible_by_default,
                },
                "column_offset_index": source_col_offset,
            }
        )

    def set_value_layout(
        self, value_layout: ValueLayoutEnum = ValueLayoutEnum.HORIZONTAL
    ) -> None:
        self.__set_pivot_value("valueLayout", value_layout.value)

    def get_pivot(self) -> dict:
        return self.__pivot_scaffold

    def reset(self) -> None:
        self.__init__(self.source_sheet_id)
