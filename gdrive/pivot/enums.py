from enum import Enum


class FilterTypeEnum(str, Enum):
    TEXT_CONTAINS = "TEXT_CONTAINS"
    TEXT_EQUALS = "TEXT_EQ"


class SortOrderEnum(str, Enum):
    ASCENDING = "ASCENDING"
    DESCENDING = "DESCENDING"


class SummarizeFunctionEnum(str, Enum):
    SUM = "SUM"


class ValueLayoutEnum(str, Enum):
    HORIZONTAL = "HORIZONTAL"
