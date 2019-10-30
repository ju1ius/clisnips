from typing import List, Optional, Tuple

import urwid

from .cell import Cell
from .column import Column


class Row(urwid.Columns):

    MIN_COLUMN_SIZE = 3
    MAX_COLUMN_SIZE = 80

    def __init__(self, columns: List[Tuple[Column, Cell]], selectable: bool = True):
        self._selectable = selectable
        cols = [(col.computed_width, cell) for col, cell in columns]
        super().__init__(cols, dividechars=1)

    def selectable(self) -> bool:
        return self._selectable

    def keypress(self, size: Tuple[int, ...], key) -> str:
        return key

    def resize(self, column_index: int, increment: int) -> Optional[int]:
        cell, options = self.contents[column_index]

        width = int(options[1]) + increment
        if width < self.MIN_COLUMN_SIZE or width > self.MAX_COLUMN_SIZE:
            return
        cell.resize(width)

        options = self.options('given', width, False)
        self.contents[column_index] = (cell, options)
        return width
