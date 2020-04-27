from typing import Union

import urwid

from clisnips.tui.urwid_types import TextMarkup
from clisnips.tui.widgets.edit import EmacsEdit
from clisnips.utils.number import get_num_decimals
from .field import Entry, SimpleField


class RangeField(SimpleField):

    def __init__(self, label: TextMarkup, *args, **kwargs):
        entry = RangeEntry(*args, **kwargs)
        super().__init__(label, entry)


class RangeEntry(Entry, EmacsEdit):

    def __init__(self, start, end, step, default=None):
        self._model = RangeModel(start, end, step, default)
        super().__init__('', str(self._model.get_value()))
        urwid.connect_signal(self, 'change', self._on_change)
        urwid.connect_signal(self, 'postchange', lambda *x: self._emit('changed'))

    def keypress(self, size, key):
        if key == '+':
            self._increment()
            return
        elif key == '-':
            self._decrement()
            return
        return super().keypress(size, key)

    def get_value(self):
        return self.get_edit_text()

    def _on_change(self, entry, value):
        self._model.set_value(value)

    def _increment(self):
        value = self.get_value()
        if not value:
            return
        self._model.set_value(value)
        self._model.increment()
        self.set_edit_text(self._model.get_value())

    def _decrement(self):
        value = self.get_value()
        if not value:
            return
        self._model.set_value(value)
        self._model.decrement()
        self.set_edit_text(self._model.get_value())


class RangeModel:

    def __init__(self, start, end, step, default=None):
        self._start = start
        self._end = end
        self._step = step
        decimals = [get_num_decimals(x) for x in (start, end, step)]
        self._num_decimals = max(decimals)
        self._is_integer = all(x == 0 for x in decimals)
        self.set_value(default if default is not None else start)

    def get_value(self) -> str:
        value = round(self._value, self._num_decimals)
        return str(value)

    def set_value(self, value: str):
        try:
            value = int(value) if self._is_integer else float(value)
        except ValueError:
            return
        self._set_numeric_value(value)

    def increment(self):
        self._set_numeric_value(self._value + self._step)

    def decrement(self):
        self._set_numeric_value(self._value - self._step)

    def _set_numeric_value(self, value: Union[int, float]):
        self._value = min(self._end, max(self._start, value))
