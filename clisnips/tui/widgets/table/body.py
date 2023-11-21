import urwid

from clisnips.tui.widgets.list_box import CyclingFocusListBox
from clisnips.tui.widgets.utils import original_widget


class Body(CyclingFocusListBox):
    KEYPRESS = 'keypress'

    _body: urwid.SimpleFocusListWalker

    def __init__(self):
        self._rows = []
        urwid.register_signal(self.__class__, self.KEYPRESS)
        super().__init__(urwid.SimpleFocusListWalker([]))

    def clear(self):
        self._body.clear()

    def append(self, row):
        self._body.append(row)

    def __iter__(self):
        yield from self._body

    @property
    def focused_row(self) -> urwid.Widget:
        row, index = self._body.get_focus()
        return original_widget(row)

    def keypress(self, size, key):
        self._emit(self.KEYPRESS, size, key)
        if key in ('up', 'down', 'left', 'right'):
            return super().keypress(size, key)
        return key
