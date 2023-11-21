import urwid

from clisnips.tui.urwid_types import TextMarkup
from clisnips.tui.widgets.edit import EmacsEdit

from .field import Entry, SimpleField


class TextField(SimpleField[str]):
    def __init__(self, label: TextMarkup, *args, **kwargs):
        entry = TextEntry(*args, **kwargs)
        super().__init__(label, entry)


class TextEntry(Entry[str], EmacsEdit):
    def __init__(self, default: str = ''):
        super().__init__('', default)
        urwid.connect_signal(self, 'postchange', lambda *x: self._emit('changed'))

    def get_value(self) -> str:
        return self.get_edit_text()
