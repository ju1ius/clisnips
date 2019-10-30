import urwid

from .cell import Cell
from .row import Row


class Body(urwid.ListBox):

    KEYPRESS = 'keypress'

    def __init__(self, column_list, cell_sizes=None, rows=None):
        self._columns = column_list
        self._cell_sizes = cell_sizes

        urwid.register_signal(self.__class__, self.KEYPRESS)
        super().__init__(urwid.SimpleFocusListWalker(rows or []))

    def set_columns(self, column_list, cell_sizes=None):
        self._columns = column_list
        self._cell_sizes = cell_sizes or []

    def update_col_width(self, col_index: int, width: int):
        self._cell_sizes[col_index] = width

    def clear(self):
        self.body.clear()

    def add_row(self, row_data):
        row = self._make_row(row_data)
        self.body.append(row)

    def __iter__(self):
        for row in self.body:
            yield row

    @property
    def focused_row(self) -> urwid.Widget:
        row, index = self.body.get_focus()
        return row.original_widget

    def _make_row(self, row_data):
        columns_count = len(self._columns)
        cols = []
        for column_number, column in enumerate(self._columns):
            value = row_data[column.index]
            separator = column_number < columns_count - 1
            cell = Cell(value, column, separator=separator)
            cols.append((column, cell))

        row = Row(cols)

        return urwid.AttrMap(row, 'default', focus_map='trow_focused')

    def keypress(self, size, key):
        """
        Emit a signal with the key and size to be handled in the parent

        The reason for this is to get the inner size of the table
        Disable only the 'up' and 'down' keys due to interfering
        with other parent pile containers
        """
        urwid.emit_signal(self, self.KEYPRESS, self, size, key)
        if key == 'up' or key == 'down':
            return
        return key
