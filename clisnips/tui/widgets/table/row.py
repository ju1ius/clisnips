import urwid

from .cell import Cell


class Row(urwid.Columns):
    def __init__(self, layout_row):
        cols = []
        for column, value in layout_row:
            cell = Cell(layout_row, column, value)
            cell = urwid.AttrMap(cell, column.attr_map)
            cols.append((column.computed_width, cell))
        super().__init__(cols, dividechars=1)

    def selectable(self) -> bool:
        return True

    def keypress(self, size: tuple[int] | tuple[int, int], key: str) -> str | None:
        return key
