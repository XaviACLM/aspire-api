from AspireAPI.Locale import Locale
from AspireAPI.sheets.AspireSheetInterface import AspireSheetInterface


class Dashboard:

    def __init__(self, sheet_interface: AspireSheetInterface, account_index, category_or_group_index):
        self._sheet = sheet_interface
        self._account_index = account_index
        self._category_or_group_index = category_or_group_index

    def balance(self, account: str) -> float:
        data = self._sheet.get("C{0}:D{0}".format(8+2*self._account_index[account]))[0][0]
        return Locale.parse_currency(data)

    def available_to_budget(self) -> float:
        data = self._sheet.get("H2")[0][0]
        return Locale.parse_currency(data)

    def spent_this_month(self) -> float:
        data = self._sheet.get("I2:J2")[0][0]
        return Locale.parse_currency(data)

    def budgeted_this_month(self) -> float:
        data = self._sheet.get("K2:L2")[0][0]
        return Locale.parse_currency(data)

    def qt_pending_transactions(self) -> float:
        data = self._sheet.get("O2")[0][0]
        return int(data)

    def available(self, category_or_group: str) -> float:
        index = self._category_or_group_index[category_or_group]
        row_index = index+6
        data = self._sheet.get("I{}".format(row_index))[0][0]
        return Locale.parse_currency(data)

    def activity(self, category_or_group: str) -> float:
        index = self._category_or_group_index[category_or_group]
        row_index = index+6
        data = self._sheet.get("L{}".format(row_index))[0][0]
        return Locale.parse_currency(data)

    def budgeted(self, category_or_group: str) -> float:
        index = self._category_or_group_index[category_or_group]
        row_index = index+6
        data = self._sheet.get("O{}".format(row_index))[0][0]
        return Locale.parse_currency(data)