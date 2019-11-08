import urwid

from .field import Entry, SimpleField
from ...urwid_types import TextMarkup


class FlagField(SimpleField):

    def __init__(self, label: TextMarkup, *args, **kwargs):
        entry = FlagEntry(*args, **kwargs)
        super().__init__(label, entry)


class FlagEntry(Entry, urwid.CheckBox):

    def __init__(self, flag: str):
        self._flag = flag
        super().__init__(flag)
        urwid.connect_signal(self, 'postchange', lambda *x: self._emit('changed'))

    def get_value(self):
        return self._flag if self.get_state() else ''
