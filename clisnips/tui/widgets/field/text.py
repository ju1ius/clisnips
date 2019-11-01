import urwid

from .field import Entry, SimpleField
from ...urwid_types import TextMarkup


class TextField(SimpleField):

    def __init__(self, label: TextMarkup, *args, **kwargs):
        entry = TextEntry(*args, **kwargs)
        super().__init__(label, entry)


class TextEntry(Entry, urwid.Edit):

    def __init__(self, default: str = ''):
        urwid.Edit.__init__(self, '', default)
        urwid.connect_signal(self, 'postchange', lambda *x: self._emit('changed'))

    def get_value(self):
        return self.get_edit_text()
