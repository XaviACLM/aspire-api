import json

from AspireAPI.Aspire import Aspire
from AspireAPI.sheets.GoogleSheetsAPI import GoogleSheetsInterface
from credentials import get_credentials

with open("personal_data.json","r") as f:
    sheet_id = json.load(f)["sheet_id"]

creds = get_credentials(["https://www.googleapis.com/auth/spreadsheets"])

gsapi = GoogleSheetsInterface(sheet_id, creds)
aspire = Aspire(gsapi, ensure_healthy=False)


def some_transaction_tests():
    fei = lambda: aspire.transactions.first_empty_index

    assert aspire.transactions[0]==aspire.transactions[-fei()]
    assert aspire.transactions[fei()] is None
    try: print(aspire.transactions[-fei()-1]); raise Exception()
    except IndexError: pass

    try: print(aspire.transactions.batch_get(-3,0)); raise Exception()
    except IndexError: pass

    assert aspire.transactions.batch_get(fei(),fei()+4)==[None]*5

    assert aspire.transactions.is_healthy()
    aspire.transactions._set(fei()+1, aspire.transactions[-1])
    assert not aspire.transactions.is_healthy()
    aspire.transactions._clear(fei()+1)
    assert aspire.transactions.is_healthy()

for group in aspire.category_groups:
    print(group,
          aspire.dashboard.activity(group),
          aspire.dashboard.available(group),
          aspire.dashboard.budgeted(group))
    for category in aspire.category_groups[group]:
        print("\t", category,
              aspire.dashboard.activity(category),
              aspire.dashboard.available(category),
              aspire.dashboard.budgeted(category))


if __name__ == '__main__':
    some_transaction_tests()
    pass
