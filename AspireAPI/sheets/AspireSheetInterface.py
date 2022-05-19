from typing import List

from AspireAPI.sheets.AspireSpreadsheetInterface import AspireSpreadsheetInterface


class AspireSheetInterface:
    """
    Provides getter and setter methods for a specific sheet in the spreadsheet underlying aspire.
    Analogous to AspireSpreadsheetInterface
    """
    def __init__(self, name, spreadsheet_interface: AspireSpreadsheetInterface):
        self._name = name
        self._spreadsheet_interface = spreadsheet_interface

    # def get(self, *args, **kwargs) -> List[list]:
    def get(self, cell_range, major_dimension="ROWS") -> List[list]:
        """
        Analogous to AspireSpreadsheetInterface.get
        """
        return self._spreadsheet_interface.get(self._name, cell_range, major_dimension=major_dimension)
        #  return self._spreadsheet_interface.get(self._name, *args, **kwargs)

    # def set(self, *args, **kwargs):
    def set(self, cell_range, data, major_dimension="ROWS"):
        """
        Analogous to AspireSpreadsheetInterface.set
        """
        return self._spreadsheet_interface.set(self._name, cell_range, data, major_dimension=major_dimension)
        # return self._spreadsheet_interface.set(self._name, *args, **kwargs)

    # def clear(self, *args, **kwargs):
    def clear(self, cell_range):
        """
        Analogous to AspireSpreadsheetInterface.clear
        """
        return self._spreadsheet_interface.clear(self._name, cell_range)
        # return self._spreadsheet_interface.clear(self._name, *args, **kwargs)
