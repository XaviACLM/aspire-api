from collections import namedtuple
from enum import Enum

from datetime import datetime as Datetime
from typing import Optional, List

from AspireAPI.Locale import Locale
from AspireAPI.sheets.AspireSheetInterface import AspireSheetInterface


class TransactionStatus(Enum):
    SETTLED = "✅"
    PENDING = "🅿️"
    UNKNOWN = "*️⃣"
    NONE = ""


Transaction = namedtuple("Transaction", "date outflow inflow category account memo status")


def row_to_transaction(row: list) -> Optional[Transaction]:
    if row==[]: return None
    date, inflow, outflow, category, account, memo, status = row
    date = Locale.parse_date(date)
    inflow = Locale.parse_currency(inflow)
    outflow = Locale.parse_currency(outflow)
    status = TransactionStatus(status)
    return Transaction(date, inflow, outflow, category, account, memo, status)


def transaction_to_row(transaction: Transaction) -> list:
    if transaction is None: return []
    date, inflow, outflow, category, account, memo, status = transaction
    date = Locale.format_date(date)
    inflow = Locale.format_currency(inflow)
    outflow = Locale.format_currency(outflow)
    status = status.value
    return [date, inflow, outflow, category, account, memo, status]


class Transactions:
    """
    Part of the API for the Transactions sheet.

    This API has the sheet behave somewhat like a stack, supporting
    - Get (.__getitem__, .batch_get)
    - Push (.push, .batch_push)
    - Pop (.pop, .batch_pop)
    - Replace (.replace, .batch_replace)

    # Indexing

    Nonnegative indices are interpreted as referring to rows, with the first one being index 0 and ascending
    indefinitely. Negative indices refer to rows, with -1 referring to the last *nonempty* row and going backwards
    from there - until the beginning of the table, at which point negative indices become invalid.

    # Private methods and the normal form

    The stack behaviour of the sheet requires that the sheet is in a particular form at the beginning (and
    also end) of each operation - namely, all rows are valid transactions an adjacent, i.e. from the first point
    that there is an empty row, there are no more non-empty rows. That this is indeed the case can be verified
    by asserting Transactions.is_healthy(). The public attribute Transaction.first_empty_index always has the index
    of the first empty row.

    Note that assuming that this state is indeed present at the start and must be kept through to the end of each
    of the eight methods above affects the implementation of these methods. More importantly, the private auxiliary
    methods for setting and clearing do not follow this philosophy - before or after their execution, the sheet
    may not be in the normal form described above. These are:
    - Generic get (._generic_get, _batch_generic_get)
    - Set (._set, ._batch_set)
    - Clear (._clear, ._batch_clear)
    """

    _TABLE_START = 9

    def __init__(self, sheet_interface: AspireSheetInterface):
        self._sheet = sheet_interface

        EXPLORE_BATCH_SIZE = 1000

        i = 0
        while True:
            result = self._sheet.get("B{}:B{}".format(Transactions._TABLE_START + EXPLORE_BATCH_SIZE * i,
                                                      Transactions._TABLE_START + EXPLORE_BATCH_SIZE * (i + 1)))
            if len(result) != EXPLORE_BATCH_SIZE:
                break
            i += 1
        self.first_empty_index = i * EXPLORE_BATCH_SIZE + len(result)

    def _localize_index(self, index: int):
        if index >= 0:
            row_index = index+Transactions._TABLE_START
        else:
            row_index = index+Transactions._TABLE_START+self.first_empty_index
        if row_index < Transactions._TABLE_START:
            raise IndexError("Tried to access an index before the start of the transactions table")
        return row_index

    def __setitem__(self, *args, **kwargs):
        raise Exception("Transactions does not support externally setting by index."
                        " Please use Transactions.push, Transactions.insert, Transactions.replace"
                        " or their batched versions."
                        " Don't use ._set or _batch_set unless you're sure you know what you're doing.")

    def _generic_get(self, index: int) -> Optional[Transaction]:
        row_index = self._localize_index(index)
        t = self._sheet.get("B{0}:H{0}".format(row_index))
        return row_to_transaction(*t) if t else None

    def _generic_batch_get(self, first_index: int, last_index: int) -> List[Optional[Transaction]]:
        if first_index > last_index:
            return []
        if first_index < 0 <= last_index:
            raise IndexError("Transactions._generic_batch_get does not support indexing"
                             " from the negative to the nonnegative part")

        row_index_1 = self._localize_index(first_index)
        row_index_2 = self._localize_index(last_index)

        ts = self._sheet.get("B{}:H{}".format(row_index_1, row_index_2))
        ts = list(map(row_to_transaction, ts))
        if len(ts) < row_index_2 - row_index_1 + 1:
            ts.extend([None] * (row_index_2 - row_index_1 + 1 - len(ts)))
        return ts

    def _set(self, index: int, transaction: Transaction, ensure_no_overwrite=True):
        if ensure_no_overwrite:
            if self._generic_get(index) is not None:
                raise Exception(
                    "Attempted to overwrite in transactions, at index"
                    " {}\n\tOriginal data:{}\n\tWritten data:{}".format(index, self[index], transaction)
                )

        row_index = self._localize_index(index)
        data = [transaction_to_row(transaction)]
        self._sheet.set("B{0}:H{0}".format(row_index), data)

    def _batch_set(self, start_index: int, transactions: List[Transaction], ensure_no_overwrite=True):
        if ensure_no_overwrite:
            end_index = start_index + len(transactions) - 1
            if self._generic_batch_get(start_index, end_index) != [None]*len(transactions):
                raise Exception(
                    "Attempted to overwrite in transactions,"
                    " from indices {} to {}".format(start_index, end_index)
                )

        row_index_1 = self._localize_index(start_index)
        row_index_2 = row_index_1+len(transactions)-1

        data = list(map(transaction_to_row, transactions))
        self._sheet.set("B{}:H{}".format(row_index_1, row_index_2), data)

    def _clear(self, index: int, ensure_nonempty=True):
        if ensure_nonempty:
            if self._generic_get(index) is None:
                raise Exception("Attempted to clear empty row @ index {}".format(index))
        row_index = self._localize_index(index)
        self._sheet.clear("B{0}:H{0}".format(row_index))

    def _batch_clear(self, first_index: int, last_index: int, ensure_nonempty=True):
        if ensure_nonempty:
            if None in self._generic_batch_get(first_index, last_index):
                raise Exception("Attempted to clear empty row between indices {}, {}".format(first_index, last_index))
        row_index_1 = self._localize_index(first_index)
        row_index_2 = self._localize_index(last_index)
        self._sheet.clear("B{}:H{}".format(row_index_1, row_index_2))

    def __getitem__(self, index: int) -> Optional[Transaction]:
        if index >= self.first_empty_index:
            return None
        return self._generic_get(index)

    def batch_get(self, first_index: int, last_index: int) -> List[Optional[Transaction]]:
        if first_index >= self.first_empty_index:
            return [None]*(last_index-first_index+1)
        if last_index >= self.first_empty_index:
            tail = [None]*(last_index-self.first_empty_index+1)
            ts = self._generic_batch_get(first_index, self.first_empty_index-1)
            ts.extend(tail)
            return ts
        return self._generic_batch_get(first_index, last_index)

    def push(self, transaction: Transaction):
        self._set(self.first_empty_index, transaction, ensure_no_overwrite=False)
        self.first_empty_index += 1

    def batch_push(self, transactions: List[Transaction]):
        self._batch_set(self.first_empty_index, transactions, ensure_no_overwrite=False)
        self.first_empty_index += len(transactions)

    def pop(self, index: int) -> Transaction:
        if index >= self.first_empty_index:
            raise Exception("Attempted to pop out of range")
        tail = self.batch_get(index, self.first_empty_index-1)
        element, *tail = tail
        self._clear(self.first_empty_index - 1, ensure_nonempty=False)
        self._batch_set(index, tail, ensure_no_overwrite=False)
        self.first_empty_index -= 1
        return element

    def batch_pop(self, first_index: int, last_index: int) -> List[Transaction]:
        if first_index > last_index:
            return []
        if first_index < 0 <= last_index:
            raise IndexError("Transactions.batch_pop does not support indexing"
                             " from the negative to the nonnegative part")
        if last_index >= self.first_empty_index:
            raise Exception("Attempted to pop out of range")

        elements = self.batch_get(first_index, last_index)
        tail = self.batch_get(last_index+1, self.first_empty_index-1)

        qt_elements = last_index-first_index+1
        self._batch_clear(self.first_empty_index - qt_elements, self.first_empty_index - 1, ensure_nonempty=False)
        self._batch_set(first_index, tail, ensure_no_overwrite=False)
        self.first_empty_index -= qt_elements
        return elements

    def insert(self, index: int, transaction: Transaction):
        if index > self.first_empty_index:
            raise Exception("Attempted to insert out of range")
        tail = self.batch_get(index, self.first_empty_index-1)
        self._set(index, transaction, ensure_no_overwrite=False)
        self._batch_set(index+1, tail, ensure_no_overwrite=False)
        self.first_empty_index += 1

    def batch_insert(self, start_index: int, transactions: List[Transaction]):
        if start_index > self.first_empty_index:
            raise Exception("Attempted to insert out of range")
        tail = self.batch_get(start_index, self.first_empty_index-1)
        self._batch_set(start_index, transactions, ensure_no_overwrite=False)
        self._batch_set(start_index+len(transactions), tail, ensure_no_overwrite=False)
        self.first_empty_index += len(transactions)

    def replace(self, index: int, transaction: Transaction):
        if index >= self.first_empty_index:
            raise Exception("Attempted to replace out of range")
        self._set(index, transaction, ensure_no_overwrite=False)

    def batch_replace(self, start_index: int, transactions: List[Transaction]):
        end_index = start_index+len(transactions)-1
        if end_index >= self.first_empty_index:
            raise Exception("Attempted to replace out of range")
        self._batch_set(start_index, transactions, ensure_no_overwrite=False)

    def is_healthy(self, safety_margin=1000):
        all_data = self._generic_batch_get(0, self.first_empty_index-1)
        if None in all_data:
            return False
        for data_first, data_second in zip(all_data, all_data[1:]):
            if data_first.date > data_second.date:
                return False
        no_data = self._generic_batch_get(self.first_empty_index, self.first_empty_index+safety_margin)
        if not all([x is None for x in no_data]):
            return False
        return True
