from __future__ import annotations

from typing import TYPE_CHECKING

import urwid
from urwid.widget.constants import WrapMode

from clisnips.tui.layouts.table import LayoutColumn

# avoid circular imports
if TYPE_CHECKING:
    from .row import Row


class Cell(urwid.Text):
    def __init__(self, row: Row, column: LayoutColumn, content):
        self._row = row
        self._column = column
        super().__init__(content, wrap=WrapMode.SPACE if column.word_wrap else WrapMode.ANY)
