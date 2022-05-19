from typing import List

from googleapiclient.discovery import build

from AspireAPI.sheets.AspireSpreadsheetInterface import AspireSpreadsheetInterface


class GoogleSheetsInterface(AspireSpreadsheetInterface):
    """
    Straightforward specification of AspireSpreadsheetInterface by means of google's actual API for google sheets
    """

    def __init__(self, spreadsheet_id, credentials):
        """
        :param spreadsheet_id: Spreadsheet id. When opening the spreadsheet, the url should be of the form
                               https://docs.google.com/spreadsheets/d/<spreadsheet-id>/<some other stuff>
        :param credentials: a google.oauth2.credentials.Credentials object.
                            Refer to google documentation for how to generate these.
        """
        self._spreadsheet_id = spreadsheet_id
        self._credentials = credentials
        self._service = build('sheets', 'v4', credentials=credentials)
        self._spreadsheets = self._service.spreadsheets()

    def get(self, sheet_name, cell_range, major_dimension="ROWS") -> List[list]:
        if " " in sheet_name:
            sheet_name = "'{}'".format(sheet_name)
        range_str = "{}!{}".format(sheet_name, cell_range)
        data = self._spreadsheets.values().get(
            spreadsheetId=self._spreadsheet_id,
            range=range_str,
            majorDimension=major_dimension
        ).execute()
        assert data["range"] == range_str
        assert data["majorDimension"] == major_dimension
        if "values" in data:
            return data["values"]
        else:
            return []

    def set(self, sheet_name, cell_range, data, major_dimension="ROWS"):
        if " " in sheet_name:
            sheet_name = "'{}'".format(sheet_name)
        range_str = "{}!{}".format(sheet_name, cell_range)
        response_obj = self._spreadsheets.values().update(
            spreadsheetId=self._spreadsheet_id,
            range=range_str,
            valueInputOption="USER_ENTERED",
            body={"values": data},
            # majorDimension=major_dimension TODO
        ).execute()
        assert response_obj["spreadsheetId"]==self._spreadsheet_id

    def clear(self, sheet_name, cell_range):
        if " " in sheet_name:
            sheet_name = "'{}'".format(sheet_name)
        range_str = "{}!{}".format(sheet_name, cell_range)
        self._spreadsheets.values().clear(
            spreadsheetId=self._spreadsheet_id,
            range=range_str,
            body=dict()
        ).execute()
