from collections import namedtuple
from enum import Enum

from datetime import datetime as Datetime
from typing import Optional, List

from AspireAPI.sheets.AspireSheetInterface import AspireSheetInterface
from AspireAPI.Locale import Locale


class CategoryTransferStatus(Enum):
    UNKNOWN = "*️⃣"
    NONE = ""


CategoryTransfer = namedtuple("CategoryTransfer", "date amount from_ to memo status")


def row_to_category_transfer(row: list) -> Optional[CategoryTransfer]:
    if row==[]: return None
    if len(row)<4: raise Exception("Badly formatted row")
    while len(row)<6:
        row.append("")
    date, amount, from_, to, memo, status = row
    date = Locale.parse_date(date)
    amount = Locale.parse_currency(amount)
    status = CategoryTransferStatus(status)
    return CategoryTransfer(date, amount, from_, to, memo, status)


def category_transfer_to_row(transfer: CategoryTransfer) -> list:
    if transfer is None: return []
    date, amount, from_, to, memo, status = transfer
    date = Locale.format_date(date)
    amount = Locale.format_currency(amount)
    status = status.value
    return [date, amount, from_, to, memo, status]


class CategoryTransfers:
    """
    Part of the API for the Category Transfers sheet.

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
    by asserting CategoryTransfers.is_healthy(). The public attribute CategoryTransfers.first_empty_index always
    has the index of the first empty row.

    Note that assuming that this state is indeed present at the start and must be kept through to the end of each
    of the eight methods above affects the implementation of these methods. More importantly, the private auxiliary
    methods for setting and clearing do not follow this philosophy - before or after their execution, the sheet
    may not be in the normal form described above. These are:
    - Generic get (._generic_get, _batch_generic_get)
    - Set (._set, ._batch_set)
    - Clear (._clear, ._batch_clear)
    """

    _TABLE_START = 8

    def __init__(self, sheet_interface: AspireSheetInterface):
        self._sheet = sheet_interface

        EXPLORE_BATCH_SIZE = 1000

        i = 0
        while True:
            result = self._sheet.get("B{}:B{}".format(CategoryTransfers._TABLE_START + EXPLORE_BATCH_SIZE * i,
                                                      CategoryTransfers._TABLE_START + EXPLORE_BATCH_SIZE * (i + 1)))
            if len(result) != EXPLORE_BATCH_SIZE:
                break
            i += 1
        self.first_empty_index = i * EXPLORE_BATCH_SIZE + len(result)

    def _localize_index(self, index: int):
        if index >= 0:
            row_index = index+CategoryTransfers._TABLE_START
        else:
            row_index = index+CategoryTransfers._TABLE_START+self.first_empty_index
        if row_index < CategoryTransfers._TABLE_START:
            raise IndexError("Tried to access an index before the start of the transactions table")
        return row_index

    def __setitem__(self, *args, **kwargs):
        raise Exception("Transactions does not support externally setting by index."
                        " Please use Transactions.push, Transactions.insert, Transactions.replace"
                        " or their batched versions."
                        " Don't use ._set or _batch_set unless you're sure you know what you're doing.")

    def _generic_get(self, index: int) -> Optional[CategoryTransfer]:
        row_index = self._localize_index(index)
        t = self._sheet.get("B{0}:G{0}".format(row_index))
        return row_to_category_transfer(*t) if t else None

    def _generic_batch_get(self, first_index: int, last_index: int) -> List[Optional[CategoryTransfer]]:
        if first_index > last_index:
            return []
        if first_index < 0 <= last_index:
            raise IndexError("Transactions._generic_batch_get does not support indexing"
                             " from the negative to the nonnegative part")

        row_index_1 = self._localize_index(first_index)
        row_index_2 = self._localize_index(last_index)

        ts = self._sheet.get("B{}:G{}".format(row_index_1, row_index_2))
        ts = list(map(row_to_category_transfer, ts))
        if len(ts) < row_index_2 - row_index_1 + 1:
            ts.extend([None] * (row_index_2 - row_index_1 + 1 - len(ts)))
        return ts

    def _set(self, index: int, transfer: CategoryTransfer, ensure_no_overwrite=True):
        if ensure_no_overwrite:
            if self._generic_get(index) is not None:
                raise Exception(
                    "Attempted to overwrite in transactions, at index"
                    " {}\n\tOriginal data:{}\n\tWritten data:{}".format(index, self[index], transfer)
                )

        row_index = self._localize_index(index)
        data = [category_transfer_to_row(transfer)]
        self._sheet.set("B{0}:G{0}".format(row_index), data)

    def _batch_set(self, start_index: int, transfers: List[CategoryTransfer], ensure_no_overwrite=True):
        if ensure_no_overwrite:
            end_index = start_index + len(transfers) - 1
            if self._generic_batch_get(start_index, end_index) != [None]*len(transfers):
                raise Exception(
                    "Attempted to overwrite in transactions,"
                    " from indices {} to {}".format(start_index, end_index)
                )

        row_index_1 = self._localize_index(start_index)
        row_index_2 = row_index_1 + len(transfers) - 1

        data = list(map(category_transfer_to_row, transfers))
        self._sheet.set("B{}:G{}".format(row_index_1, row_index_2), data)

    def _clear(self, index: int, ensure_nonempty=True):
        if ensure_nonempty:
            if self._generic_get(index) is None:
                raise Exception("Attempted to clear empty row @ index {}".format(index))
        row_index = self._localize_index(index)
        self._sheet.clear("B{0}:G{0}".format(row_index))

    def _batch_clear(self, first_index: int, last_index: int, ensure_nonempty=True):
        if ensure_nonempty:
            if None in self._generic_batch_get(first_index, last_index):
                raise Exception("Attempted to clear empty row between indices {}, {}".format(first_index, last_index))
        row_index_1 = self._localize_index(first_index)
        row_index_2 = self._localize_index(last_index)
        self._sheet.clear("B{}:G{}".format(row_index_1, row_index_2))

    def __getitem__(self, index: int) -> Optional[CategoryTransfer]:
        if index >= self.first_empty_index:
            return None
        return self._generic_get(index)

    def batch_get(self, first_index: int, last_index: int) -> List[Optional[CategoryTransfer]]:
        if first_index >= self.first_empty_index:
            return [None]*(last_index-first_index+1)
        if last_index >= self.first_empty_index:
            tail = [None]*(last_index-self.first_empty_index+1)
            ts = self._generic_batch_get(first_index, self.first_empty_index-1)
            ts.extend(tail)
            return ts
        return self._generic_batch_get(first_index, last_index)

    def push(self, transfer: CategoryTransfer):
        self._set(self.first_empty_index, transfer, ensure_no_overwrite=False)
        self.first_empty_index += 1

    def batch_push(self, transfers: List[CategoryTransfer]):
        self._batch_set(self.first_empty_index, transfers, ensure_no_overwrite=False)
        self.first_empty_index += len(transfers)

    def pop(self, index: int) -> CategoryTransfer:
        if index >= self.first_empty_index:
            raise Exception("Attempted to pop out of range")
        tail = self.batch_get(index, self.first_empty_index-1)
        element, *tail = tail
        self._clear(self.first_empty_index - 1, ensure_nonempty=False)
        self._batch_set(index, tail, ensure_no_overwrite=False)
        self.first_empty_index -= 1
        return element

    def batch_pop(self, first_index: int, last_index: int) -> List[CategoryTransfer]:
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

    def insert(self, index: int, transfer: CategoryTransfer):
        if index > self.first_empty_index:
            raise Exception("Attempted to insert out of range")
        tail = self.batch_get(index, self.first_empty_index-1)
        self._set(index, transfer, ensure_no_overwrite=False)
        self._batch_set(index+1, tail, ensure_no_overwrite=False)
        self.first_empty_index += 1

    def batch_insert(self, start_index: int, transfers: List[CategoryTransfer]):
        if start_index > self.first_empty_index:
            raise Exception("Attempted to insert out of range")
        tail = self.batch_get(start_index, self.first_empty_index-1)
        self._batch_set(start_index, transfers, ensure_no_overwrite=False)
        self._batch_set(start_index + len(transfers), tail, ensure_no_overwrite=False)
        self.first_empty_index += len(transfers)

    def replace(self, index: int, transfer: CategoryTransfer):
        if index >= self.first_empty_index:
            raise Exception("Attempted to replace out of range")
        self._set(index, transfer, ensure_no_overwrite=False)

    def batch_replace(self, start_index: int, transfers: List[CategoryTransfer]):
        end_index = start_index + len(transfers) - 1
        if end_index >= self.first_empty_index:
            raise Exception("Attempted to replace out of range")
        self._batch_set(start_index, transfers, ensure_no_overwrite=False)

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
