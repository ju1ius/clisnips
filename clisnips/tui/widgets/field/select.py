from typing import Iterable, Optional

import urwid

from .field import Entry, SimpleField
from ..combobox import ComboBox
from ...urwid_types import TextMarkup


class SelectField(SimpleField):

    def __init__(self, label: TextMarkup, *args, **kwargs):
        entry = SelectEntry(*args, **kwargs)
        super().__init__(label, entry)


class SelectEntry(Entry, ComboBox):

    def __init__(self, choices: Optional[Iterable[str]] = None, default: int = 0):
        super().__init__()
        if choices:
            for i, choice in enumerate(choices):
                self.append(choice, choice, i == default)

    def get_value(self):
        return self.get_selected()
