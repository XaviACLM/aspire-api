from typing import List


class AspireSpreadsheetInterface:
    """
    Provides (batch) getter and setter methods for the actual google spreadsheet underlying Aspire.

    This is essentially meant to abstract the functionalities of its always-used-in-practice subclass, GoogleSheetsAPI.
    This is the reason for the strange quirks of implementation, re: return format and such.
    """

    def get(self, sheet_name, cell_range, major_dimension="ROWS") -> List[list]:
        """
        :param sheet_name: name of the specific sheet (within the spreadsheet) where the command will be executed
        :param cell_range: range of cells in A1 notation (https://developers.google.com/sheets/api/guides/concepts)
        :param major_dimension: whether the return will be in row-major or column-major order
        :return: a list, each element corresponding to the elements of a major_dimension (row, column) in the queried
                 range. Empty trailing cells/major_dimensions are removed.
        """
        raise NotImplementedError()

    def set(self, sheet_name, cell_range, data, major_dimension="ROWS"):
        """
        :param sheet_name: name of the specific sheet (within the spreadsheet) where the command will be executed
        :param cell_range: range of cells in A1 notation (https://developers.google.com/sheets/api/guides/concepts)
        :param major_dimension: whether the data given is in row-major or column-major order
        :param data: a list, each element corresponding to the elements of a major_dimension (row, column) to be
                     inserted in the range. empty trailing elements may be omitted.

        Elements are to be set according to the USER_ENTERED value input option in the google sheets API docs, that is,
        the elements fed through data appear in the spreadsheet as if though they had been manually typed in (which may
        beget parsing/formatting by sheets - turning a 12 into 12.00€, and such)

        May throw an exception if the data does not fit into the provided range.
        """
        raise NotImplementedError()

    def clear(self, sheet_name, cell_range):
        """
        :param sheet_name: name of the specific sheet (within the spreadsheet) where the command will be executed
        :param cell_range: range of cells in A1 notation (https://developers.google.com/sheets/api/guides/concepts)

        Clears the content (but not the formatting) of all cells in the provided range
        """
        raise NotImplementedError()
