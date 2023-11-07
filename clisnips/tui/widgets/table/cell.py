from __future__ import annotations
from typing import TYPE_CHECKING

import urwid
from urwid.widget.constants import WrapMode

# avoid circular imports
if TYPE_CHECKING:
    from .column import Column
    from .row import Row


class Cell(urwid.Text):

    def __init__(self, row: Row, column: Column, content):
        self._row = row
        self._column = column
        super().__init__(content, wrap=WrapMode.SPACE if column.word_wrap else WrapMode.ANY)
