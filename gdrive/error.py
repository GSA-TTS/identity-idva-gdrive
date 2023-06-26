"""
Custom Export Error. For specific raise/catch use.
"""


class ExportError(Exception):
    def __init__(self, message):
        super().__init__(message)
