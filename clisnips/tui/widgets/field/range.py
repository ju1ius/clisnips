import urwid

from .field import Entry, SimpleField
from ..edit import EmacsEdit
from ...urwid_types import TextMarkup


class RangeField(SimpleField):

    def __init__(self, label: TextMarkup, *args, **kwargs):
        entry = RangeEntry(*args, **kwargs)
        super().__init__(label, entry)


class RangeEntry(Entry, EmacsEdit):
    """TODO: implement real range widget !"""

    def __init__(self, start, end, step, default=None):
        super().__init__('', default or '')
        urwid.connect_signal(self, 'postchange', lambda *x: self._emit('changed'))

    def get_value(self):
        return self.get_edit_text()
