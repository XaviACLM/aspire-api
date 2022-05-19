import json

from AspireAPI.Aspire import Aspire
from AspireAPI.sheets.GoogleSheetsAPI import GoogleSheetsInterface
from credentials import get_credentials



def some_transaction_tests(aspire: Aspire):
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


def some_category_transfer_tests(aspire: Aspire):
    fei = lambda: aspire.category_transfers.first_empty_index

    assert aspire.category_transfers[0]==aspire.category_transfers[-fei()]
    assert aspire.category_transfers[fei()] is None
    try: print(aspire.category_transfers[-fei()-1]); raise Exception()
    except IndexError: pass

    try: print(aspire.category_transfers.batch_get(-3,0)); raise Exception()
    except IndexError: pass

    assert aspire.category_transfers.batch_get(fei(),fei()+4)==[None]*5

    assert aspire.category_transfers.is_healthy()
    aspire.category_transfers._set(fei()+1, aspire.category_transfers[-1])
    assert not aspire.category_transfers.is_healthy()
    aspire.category_transfers._clear(fei()+1)
    assert aspire.category_transfers.is_healthy()


def some_category_grouping_tests(aspire: Aspire):
    for group in aspire.category_groups:
        activity = aspire.dashboard.activity(group)
        available = aspire.dashboard.available(group)
        budgeted = aspire.dashboard.budgeted(group)
        for category in aspire.category_groups[group]:
            activity -= aspire.dashboard.activity(category)
            available -= aspire.dashboard.available(category)
            budgeted -= aspire.dashboard.budgeted(category)
        assert abs(activity)+abs(available)+abs(budgeted)<1e-10


if __name__ == '__main__':
    with open("personal_data.json", "r") as f:
        sheet_id = json.load(f)["sheet_id"]

    creds = get_credentials(["https://www.googleapis.com/auth/spreadsheets"])

    gsapi = GoogleSheetsInterface(sheet_id, creds)
    aspire = Aspire(gsapi, ensure_healthy=False)

    some_transaction_tests(aspire)
    some_category_transfer_tests(aspire)
    some_category_grouping_tests(aspire)