from collections.abc import Iterable
from decimal import Decimal
from typing import TypeAlias

from clisnips.tui.urwid_types import TextMarkup
from clisnips.tui.widgets.combobox import ComboBox

from .field import Entry, SimpleField


Value: TypeAlias = str | Decimal


class SelectField(SimpleField[Value]):
    def __init__(self, label: TextMarkup, *args, **kwargs):
        entry = SelectEntry(*args, **kwargs)
        super().__init__(label, entry)


class SelectEntry(Entry[Value], ComboBox[Value]):
    def __init__(self, choices: Iterable[Value] | None = None, default: int = 0):
        super().__init__()
        if choices:
            for i, choice in enumerate(choices):
                self.append(str(choice), choice, i == default)

    def get_value(self) -> Value:
        # TODO: this may need to be generic
        return self.get_selected() or ''
