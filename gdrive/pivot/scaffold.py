from abc import ABC, abstractmethod


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
    def __init__(self, value: str):
        pass

    @abstractmethod
    def get_scaffold(self) -> dict:
        """
        Returns internal scaffold

        Returns:
            dict: this dict represents Google Sheets API conforming JSON
        """
        pass


class UserEnteredValueScaffold(AbstractScaffold):
    """
    User Entered Values are parsed by the Google Sheets API as if
    the end user typed the value in from the keyboard, and are subject to
    the same pre-processing as in such cases. This can be helpful when trying
    to emulate the side effects of manually entering in values, as one might when
    attempting to recreate a pivot table programatically.

    Args:
        AbstractScaffold (ABC): Sets interface for AbstractScaffoldClasses
    """

    def __init__(self, value: str):
        """
        Scaffolds a value, as if the user typed it into a spreadsheet

        Args:
            value (str): Desired Value
        """
        self.__scaffold = {"userEnteredValue": value}

    def get_scaffold(self) -> dict:
        return self.__scaffold
