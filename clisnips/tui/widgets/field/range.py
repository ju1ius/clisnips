from decimal import Decimal
import urwid

from clisnips.tui.urwid_types import TextMarkup
from clisnips.tui.widgets.edit import EmacsEdit
from clisnips.utils.number import get_num_decimals

from .field import Entry, SimpleField


class RangeField(SimpleField):
    def __init__(self, label: TextMarkup, *args, **kwargs):
        entry = RangeEntry(*args, **kwargs)
        super().__init__(label, entry)


class RangeEntry(Entry[Decimal], EmacsEdit):
    def __init__(self, start: Decimal, end: Decimal, step: Decimal, default: Decimal | None = None):
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

    def get_value(self) -> Decimal:
        return self._model.get_numeric_value()

    def _on_change(self, entry, value):
        self._model.set_value(value)

    def _increment(self):
        value = self.get_edit_text()
        if not value:
            return
        self._model.set_value(value)
        self._model.increment()
        self.set_edit_text(self._model.get_value())

    def _decrement(self):
        value = self.get_edit_text()
        if not value:
            return
        self._model.set_value(value)
        self._model.decrement()
        self.set_edit_text(self._model.get_value())


class RangeModel:
    def __init__(self, start: Decimal, end: Decimal, step: Decimal, default: Decimal | None = None):
        self._start = start
        self._end = end
        self._step = step
        decimals = [get_num_decimals(x) for x in (start, end, step)]
        self._num_decimals = max(decimals)
        self._value: Decimal = Decimal('0')
        self.set_numeric_value(default if default is not None else start)

    def get_value(self) -> str:
        return str(self.get_numeric_value())

    def set_value(self, value: str):
        try:
            v = Decimal(value)
        except Exception:
            return
        self.set_numeric_value(v)

    def get_numeric_value(self) -> Decimal:
        return round(self._value, self._num_decimals)

    def set_numeric_value(self, value: Decimal):
        self._value = min(self._end, max(self._start, value))

    def increment(self):
        self.set_numeric_value(self._value + self._step)

    def decrement(self):
        self.set_numeric_value(self._value - self._step)
