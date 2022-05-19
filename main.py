import json
from datetime import datetime as Datetime

from AspireAPI.Aspire import Aspire
from AspireAPI.CategoryTransfers import CategoryTransfer, CategoryTransferStatus
from AspireAPI.Locale import Locale
from AspireAPI.Transactions import Transaction, TransactionStatus
from AspireAPI.sheets.ThrottledSpreadsheetInterface import ThrottledSpreadsheetInterface
from AspireAPI.sheets.GoogleSheetsAPI import GoogleSheetsInterface
from credentials import get_credentials

with open("personal_data.json","r") as f:
    sheet_id = json.load(f)["sheet_id"]

creds = get_credentials(["https://www.googleapis.com/auth/spreadsheets"])

my_normal_account="FAKEBANK1"
my_savings_account="FAKEBANK2"

gsapi = GoogleSheetsInterface(sheet_id, creds)
tgsapi = ThrottledSpreadsheetInterface(60, 60, gsapi)
aspire = Aspire(tgsapi, ensure_healthy=False)

budgeted_categories = [c for c in aspire.categories if aspire.category_amount(c) is not None]

available_to_budget = aspire.dashboard.available_to_budget()
remainder_to_budget = {category:aspire.category_amount(category)-aspire.dashboard.available(category)
                       for category in budgeted_categories}

remainder_after_budgeting = available_to_budget - sum(remainder_to_budget.values())
if remainder_after_budgeting < 0:
    print("Not enough available-to-budget money to fill every category")
    raise SystemExit()

today = Datetime.today()
transfers = []
for category in budgeted_categories:
    transfers.append(CategoryTransfer(today, remainder_to_budget[category],
                                      "Available to budget", category, "", CategoryTransferStatus.NONE))
transfers.append(CategoryTransfer(today,remainder_after_budgeting,
                                  "Available to budget", "Savings", "", CategoryTransferStatus.NONE))

transactions = [
    Transaction(today, remainder_after_budgeting, 0, "↕️ Account Transfer", my_normal_account, "", TransactionStatus.PENDING),
    Transaction(today, 0, remainder_after_budgeting, "↕️ Account Transfer", my_savings_account, "", TransactionStatus.PENDING)
]

aspire.category_transfers.batch_push(transfers)
aspire.transactions.batch_push(transactions)

print("Remember to go transfer {} from {} to {} and mark the first transaction as settled".format(
    Locale.format_currency(remainder_after_budgeting), my_normal_account, my_savings_account
))