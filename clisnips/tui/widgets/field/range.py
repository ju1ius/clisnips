import urwid

from .field import SimpleField, Entry
from ...urwid_types import TextMarkup


class RangeField(SimpleField):

    def __init__(self, label: TextMarkup, *args, **kwargs):
        entry = RangeEntry(*args, **kwargs)
        super().__init__(label, entry)


class RangeEntry(Entry, urwid.Edit):
    """TODO: implement real range widget !"""

    def __init__(self, start, end, step, default=None):
        urwid.Edit.__init__(self, '', default or '')
        urwid.connect_signal(self, 'postchange', lambda *x: self._emit('changed'))

    def get_value(self):
        return self.get_edit_text()
