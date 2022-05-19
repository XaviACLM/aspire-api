from typing import List, Union
from datetime import timedelta as TimeDelta
from datetime import datetime as DateTime
from time import sleep

from AspireAPI.sheets.AspireSpreadsheetInterface import AspireSpreadsheetInterface


class ThrottledSpreadsheetInterface(AspireSpreadsheetInterface):
    """
    Straightforward specification of AspireSpreadsheetInterface by means of google's actual API for google sheets
    """

    def __init__(self, time_horizon: Union[TimeDelta, int, float], max_queries: int,
                 interface: AspireSpreadsheetInterface):
        """
        :param spreadsheet_id: Spreadsheet id. When opening the spreadsheet, the url should be of the form
                               https://docs.google.com/spreadsheets/d/<spreadsheet-id>/<some other stuff>
        :param credentials: a google.oauth2.credentials.Credentials object.
                            Refer to google documentation for how to generate these.
        """
        self._interface = interface
        self.time_horizon = time_horizon
        self.max_queries = max_queries

        if not isinstance(time_horizon, TimeDelta):
            time_horizon = TimeDelta(seconds=time_horizon)
        self._query_times = [DateTime.now() - time_horizon for _ in range(max_queries)]
        self._query_pointer = 0

    def _throttle(self):
        now = DateTime.now()
        then = self._query_times[self._query_pointer]
        if now - then < self.time_horizon:
            sleep((self.time_horizon - (now - then)).total_seconds())
        self._query_times[self._query_pointer] = now
        self._query_pointer = (self._query_pointer + 1) % self.max_queries

    def get(self, sheet_name, cell_range, major_dimension="ROWS") -> List[list]:
        self._throttle()
        return self._interface.get(sheet_name, cell_range, major_dimension=major_dimension)

    def set(self, sheet_name, cell_range, data, major_dimension="ROWS"):
        self._throttle()
        return self._interface.set(sheet_name, cell_range, data, major_dimension=major_dimension)

    def clear(self, sheet_name, cell_range):
        self._throttle()
        return self._interface.clear(sheet_name, cell_range)
