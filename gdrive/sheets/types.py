from abc import ABC, abstractmethod
from enum import Enum


class FilterTypeEnum(str, Enum):
    TEXT_CONTAINS = "TEXT_CONTAINS"
    TEXT_EQUALS = "TEXT_EQ"
    CUSTOM = "CUSTOM_FORMULA"


class SortOrderEnum(str, Enum):
    ASCENDING = "ASCENDING"
    DESCENDING = "DESCENDING"


class SummarizeFunctionEnum(str, Enum):
    SUM = "SUM"


class ValueLayoutEnum(str, Enum):
    HORIZONTAL = "HORIZONTAL"


class FormulaEnum(str, Enum):
    NOOP = ""
    OR = "OR"
    SUM = "sum"
    REGEX_MATCH = "regexmatch"
    GET_PIVOT_DATA = "GETPIVOTDATA"


class StringLiteral:
    def __init__(self, value) -> None:
        self.value = value

    def __str__(self) -> str:
        return '"%s"' % (self.value)


class Range:
    def __init__(self, a, b) -> None:
        self.a = a
        self.b = b

    def __str__(self) -> str:
        return "%s:%s" % (self.a, self.b)


class AbstractScaffold(ABC):
    """
    Client code may use classes like UserEnteredValue to add scaffolds to filter
    criterion builder. This supports cases where filter criterion may have large
    numbers of acceptable scaffolds that may be arbitrarily combined. We use
    AbstractScaffold to ensure type safety in the abritary lists

    Args:
        ABC (AbstractBaseClass): ABC provided base class for Abstract classes
    """

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def get_scaffold(self) -> dict:
        """
        Returns internal scaffold

        Returns:
            dict: this dict represents Google Sheets API conforming JSON
        """
        pass


class UserEnteredValue(AbstractScaffold):
    """
    User Entered Values are parsed by the Google Sheets API as if
    the end user typed the value in from the keyboard, and are subject to
    the same pre-processing as in such cases. This can be helpful when trying
    to emulate the side effects of manually entering in values, as one might when
    attempting to recreate a pivot table programatically.

    Args:
        AbstractScaffold (ABC): Sets interface for AbstractScaffoldClasses
    """

    def __init__(self, value):
        """
        Scaffolds a value, as if the user typed it into a spreadsheet

        Args:
            value (ANY): Desired Value. toString is called to encode
                this value into the internal scaffold
        """
        self.__scaffold = {"userEnteredValue": str(value)}

    def get_scaffold(self) -> dict:
        return self.__scaffold
