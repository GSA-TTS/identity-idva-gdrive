import json
from munch import DefaultMunch

from gdrive.pivot.enums import (
    FilterTypeEnum,
    SortOrderEnum,
    SummarizeFunctionEnum,
    ValueLayoutEnum,
)
from gdrive.pivot.scaffold import AbstractScaffold


class PivotTableBuilder:
    def __init__(self, source_sheet_id: int = 0, col_lookup=None) -> None:
        self.source_sheet_id = source_sheet_id
        self.columns = col_lookup
        self.__pivot_scaffold = {
            "pivotTable": {
                "source": {
                    # First Sheet (Sheet1) is always ID 0
                    "sheetId": source_sheet_id,
                },
            }
        }

    def __get_pivot_value(self, field: str) -> dict or None:
        if field not in self.__pivot_scaffold["pivotTable"]:
            return None

        return self.__pivot_scaffold["pivotTable"][field]

    def __set_pivot_value(self, field: str, value: any) -> None:
        self.__pivot_scaffold["pivotTable"][field] = value

    def __get_column_id(self, column_name: str):
        if column_name not in self.columns:
            raise ValueError("Column name %s does not exist" % (column_name))

        return self.columns[column_name]

    def add_row(
        self,
        source_col: str,
        sortOrder: SortOrderEnum,
        show_totals: bool = True,
    ) -> None:
        col_idx = self.__get_column_id(source_col)
        self.add_row_from_offset(col_idx, sortOrder, show_totals)

    def add_row_from_offset(
        self,
        source_col_offset: int,
        sortOrder: SortOrderEnum,
        show_totals: bool = True,
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
        source_col: str,
        summarize_func: SummarizeFunctionEnum,
    ) -> None:
        col_idx = self.__get_column_id(source_col)
        self.add_value_from_offset(col_idx, summarize_func)

    def add_value_from_offset(
        self,
        source_col_offset: int,
        summarize_func: SummarizeFunctionEnum,
    ) -> None:
        if self.__get_pivot_value("values") is None:
            self.__set_pivot_value("values", [])

        self.__get_pivot_value("values").append(
            {
                "summarizeFunction": summarize_func.value,
                "sourceColumnOffset": source_col_offset,
            }
        )

    def add_filter(
        self,
        source_col: str,
        filter_type: FilterTypeEnum,
        values: [AbstractScaffold],
        visible_by_default: bool = True,
    ) -> None:
        col_idx = self.__get_column_id(source_col)
        self.add_filter_from_offset(col_idx, filter_type, values, visible_by_default)

    def add_filter_from_offset(
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
                        "values": [val.get_scaffold() for val in values],
                    },
                    "visibleByDefault": visible_by_default,
                },
                "columnOffsetIndex": source_col_offset,
            }
        )

    def set_value_layout(
        self, value_layout: ValueLayoutEnum = ValueLayoutEnum.HORIZONTAL
    ) -> None:
        self.__set_pivot_value("valueLayout", value_layout.value)

    def as_dict(self) -> dict:
        return self.__pivot_scaffold

    def as_json(self) -> str:
        return json.dumps(self.__pivot_scaffold)

    def as_object(self) -> object:
        return DefaultMunch.fromDict(self.__pivot_scaffold)

    def reset(self) -> None:
        self.__init__(self.source_sheet_id)
