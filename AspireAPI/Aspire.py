from itertools import chain

from AspireAPI.CategoryTransfers import CategoryTransfers
from AspireAPI.Dashboard import Dashboard
from AspireAPI.Locale import Locale
from AspireAPI.Transactions import Transactions
from AspireAPI.sheets.AspireSheetInterface import AspireSheetInterface
from AspireAPI.sheets.AspireSpreadsheetInterface import AspireSpreadsheetInterface


class Aspire:
    def __init__(self, spreadsheet_interface: AspireSpreadsheetInterface,
                 ensure_healthy = True,
                 dashboard_sheetname="Dashboard",
                 category_transfers_sheetname="Category Transfers",
                 transactions_sheetname="Transactions",
                 configuration_sheetname="Configuration"):

        self._spreadsheet = spreadsheet_interface

        self.dashboard_sheetname = dashboard_sheetname
        self.category_transfers_sheetname = category_transfers_sheetname
        self.transactions_sheetname = transactions_sheetname
        self.configuration_sheetname = configuration_sheetname

        self._ensure_healthy = ensure_healthy

        self._transactions = None
        self._category_transfers = None
        self._dashboard = None
        self._load_configuration()

    @property
    def transactions(self):
        if self._transactions is None:
            self._transactions_sheet = AspireSheetInterface(self.transactions_sheetname, self._spreadsheet)
            self._transactions = Transactions(self._transactions_sheet)
            if self._ensure_healthy and not self._transactions.is_healthy():
                raise Exception("Transactions sheet is not in the required format")
        return self._transactions

    @property
    def category_transfers(self):
        if self._category_transfers is None:
            self._category_transfers_sheet = AspireSheetInterface(self.category_transfers_sheetname, self._spreadsheet)
            self._category_transfers = CategoryTransfers(self._category_transfers_sheet)
            if self._ensure_healthy and not self._category_transfers.is_healthy():
                raise Exception("Transactions sheet is not in the required format")
        return self._category_transfers

    @property
    def dashboard(self):
        if self._dashboard is None:
            self._dashboard_sheet = AspireSheetInterface(self.dashboard_sheetname, self._spreadsheet)
            self._dashboard = Dashboard(self._dashboard_sheet, self._account_index, self._category_or_group_index)
        return self._dashboard

    def _load_configuration(self):
        self._configuration_sheet = AspireSheetInterface(self.configuration_sheetname, self._spreadsheet)
        self._account_index = dict()
        self._category_or_group_index = dict()
        self.reload_configuration()

    def reload_configuration(self, total_rows = 109):
        self.monthly_income = Locale.parse_currency(self._configuration_sheet.get("B5:C5")[0][0])
        self.unallocated_income = Locale.parse_currency(self._configuration_sheet.get("D5")[0][0])
        self.half_year_fund = Locale.parse_currency(self._configuration_sheet.get("E5:F5")[0][0])

        deflate_dims = lambda l: [e[0] for e in l if len(e)>0]
        self.accounts = deflate_dims(self._configuration_sheet.get("H9:H23"))
        self.credit_cards = deflate_dims(self._configuration_sheet.get("I9:I23"))
        self.asset_categories = deflate_dims(self._configuration_sheet.get("H28:H35"))
        self.debt_categories = deflate_dims(self._configuration_sheet.get("I28:I35"))
        self.hidden_categories = deflate_dims(self._configuration_sheet.get("H42:H86"))
        self.hidden_accounts = deflate_dims(self._configuration_sheet.get("H93:H107"))

        self._account_index.clear()
        for index, account in enumerate(chain(self.accounts, self.credit_cards)):
            self._account_index[account] = index

        category_data = self._configuration_sheet.get("B9:F{}".format(total_rows-1))
        header_symbol = "✦"
        tick_symbol = "✓"

        self._category_data = dict()
        self.category_groups = {None:[]}
        self._category_or_group_index.clear()
        latest_header = None
        for index, item in enumerate(category_data):
            if item==[]:
                continue
            if item[0] == header_symbol:
                latest_header = item[1]
                if latest_header in self.category_groups:
                    raise Exception("Repeated category group in configuration sheet")
                self.category_groups[item[1]] = []
                self._category_or_group_index[latest_header] = index
                continue
            while len(item)<5:
                item.append("")
            symbol, name, amt, goal, is_necessary = item
            self.category_groups[latest_header].append(name)
            self._category_or_group_index[name] = index
            self._category_data[name] = (index, symbol,
                                         None if amt == "" else Locale.parse_currency(amt),
                                         None if goal == "" else Locale.parse_currency(goal),
                                         is_necessary == tick_symbol)

        if self.category_groups[None]==[]:
            self.category_groups.pop(None)
        self.categories = list(self._category_data.keys())

    def category_symbol(self, category):
        return self._category_data[category][1]

    def category_amount(self, category):
        return self._category_data[category][2]

    def category_goal(self, category):
        return self._category_data[category][3]

    def is_category_necessary(self, category):
        return self._category_data[category][4]
