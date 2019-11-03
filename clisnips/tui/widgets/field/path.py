from typing import Optional

import urwid

from .field import Entry, SimpleField
from ..edit import EmacsEdit
from ...urwid_types import TextMarkup
from ...._types import AnyPath


class PathField(SimpleField):

    def __init__(self, label: TextMarkup, *args, **kwargs):
        entry = PathEntry(*args, **kwargs)
        super().__init__(label, entry)


class PathEntry(Entry, EmacsEdit):
    """TODO: implement fs path completion !"""

    def __init__(self, cwd: Optional[AnyPath] = None, mode: str = '', default: str = ''):
        super().__init__('', default)
        urwid.connect_signal(self, 'postchange', lambda *x: self._emit('changed'))

    def get_value(self):
        return self.get_edit_text()
