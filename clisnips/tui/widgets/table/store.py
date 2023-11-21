import enum
from collections.abc import Callable
from typing import Any

import urwid


class TableStore:
    class Signals(enum.StrEnum):
        ROWS_LOADED = 'rows-loaded'
        ROW_UPDATED = 'row-updated'
        ROW_INSERTED = 'row-inserted'
        ROW_DELETED = 'row-deleted'

    def __init__(self):
        self._rows = []
        urwid.register_signal(self.__class__, list(self.Signals))

    def load(self, rows):
        self._rows = rows
        self.emit(self.Signals.ROWS_LOADED)

    def update(self, index, row):
        self._rows[index] = row
        self.emit(self.Signals.ROW_UPDATED, index, row)

    def insert(self, index, row):
        self._rows.insert(index, row)
        self.emit(self.Signals.ROW_INSERTED, index, row)

    def append(self, row):
        self._rows.append(row)
        self.emit(self.Signals.ROW_INSERTED, len(self._rows) - 1, row)

    def delete(self, index):
        self._rows.pop(index)
        self.emit(self.Signals.ROW_DELETED, index)

    def find(self, callback: Callable[[Any], bool]) -> tuple[int, Any] | tuple[None, None]:
        for index, row in enumerate(self._rows):
            if callback(row):
                return index, row
        return None, None

    @property
    def rows(self):
        return self._rows

    def emit(self, signal: Signals, *args):
        urwid.emit_signal(self, signal, self, *args)

    def connect(self, signal: Signals, callback):
        urwid.connect_signal(self, signal, callback)

    def __getitem__(self, key: int | slice):
        if isinstance(key, int | slice):
            return self._rows[key]
        raise TypeError(f'Table store indices must be int or slice, not {type(key).__name__}')

    def __len__(self):
        return len(self._rows)

    def __iter__(self):
        return iter(self._rows)
