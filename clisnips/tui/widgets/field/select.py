from collections.abc import Iterable

from clisnips.tui.urwid_types import TextMarkup
from clisnips.tui.widgets.combobox import ComboBox

from .field import Entry, SimpleField


class SelectField(SimpleField[str]):
    def __init__(self, label: TextMarkup, *args, **kwargs):
        entry = SelectEntry(*args, **kwargs)
        super().__init__(label, entry)


class SelectEntry(Entry[str], ComboBox[str]):
    def __init__(self, choices: Iterable[str] | None = None, default: int = 0):
        super().__init__()
        if choices:
            for i, choice in enumerate(choices):
                self.append(choice, choice, i == default)

    def get_value(self) -> str:
        # TODO: this may need to be generic
        return self.get_selected() or ''
