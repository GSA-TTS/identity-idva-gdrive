from abc import ABC, abstractmethod
from enum import Enum


"""
This types module provides intellisense and strong(er) typing 
when using the Pivot and Formula builder interfaces. If a function is 
needed and the below enum do not support it, please add it to keep this 
module up to date and useful.     
"""


class FilterTypeEnum(str, Enum):
    """
    FilterType provides filter function names for use with the Pivot and Formula
    builders
    """

    TEXT_CONTAINS = "TEXT_CONTAINS"
    TEXT_EQUALS = "TEXT_EQ"
    CUSTOM = "CUSTOM_FORMULA"


class SortOrderEnum(str, Enum):
    """
    SortOrderEnum provides sort order names for use with the Pivot and Formula
    builders
    """

    ASCENDING = "ASCENDING"
    DESCENDING = "DESCENDING"


class SummarizeFunctionEnum(str, Enum):
    """
    Summarize provides summary functions for use with the
    Pivot and Formula builders
    """

    SUM = "SUM"


class ValueLayoutEnum(str, Enum):
    """
    ValueLayout provides value layout names for use with the Pivot and Formula
    builders
    """

    HORIZONTAL = "HORIZONTAL"


class FormulaEnum(str, Enum):
    """
    FormulaEnum provides formula names for use with the Pivot and Formula
    builders
    """

    NOOP = ""
    OR = "OR"
    SUM = "sum"
    REGEX_MATCH = "regexmatch"
    GET_PIVOT_DATA = "GETPIVOTDATA"


class StringLiteral:
    """
    StringLiteral allows string values to be render as literal strings in the resulting
    Function or Pivot scaffold. i.e. "Hello world!" is a string literal.

    Use string literals where the use of a token (eventName) is not desired in the
    Function or Pivot Scaffold
    """

    def __init__(self, value) -> None:
        self.value = value

    def __str__(self) -> str:
        return '"%s"' % (self.value)


class Range:
    """
    Range provides a scaffold for a range string between two string
    values. (i.e. A2:G5)
    """

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
