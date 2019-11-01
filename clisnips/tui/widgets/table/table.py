import urwid

from .body import Body
from .column import Column
from .input_processor import InputProcessor, Direction
from .store import Store
from .table_layout import TableLayout


class Table(urwid.Frame):
    SIGNAL_ROW_SELECTED = 'row-selected'
    SIGNAL_COLUMN_RESIZED = 'column_resized'
    SIGNALS = [SIGNAL_ROW_SELECTED, SIGNAL_COLUMN_RESIZED]

    def __init__(self, model: Store):
        self._model = model
        self._columns = []
        self._layout = TableLayout()
        self._rowcount = len(self._model)
        # self._header = Header(self._model.columns)
        self._body = Body(column_list=[], cell_sizes=[])
        urwid.connect_signal(self._body, 'keypress', self._on_body_keypress)

        self._footer = urwid.Text('')

        self._widget_size = (0, 0)
        self._visible_columns = 0
        self._focused_row_index = 0
        self._focused_col_index = 0
        self._input_processor = InputProcessor()

        for row in self._model:
            self._body.add_row(row)

        urwid.connect_signal(model, model.Signals.ROWS_LOADED, self.refresh)

        super().__init__(
            self._body,
            # urwid.AttrMap(self._header, 'thead'),
            # urwid.AttrMap(self._footer, 'tfoot')
        )
        urwid.register_signal(self.__class__, self.SIGNALS)
        # self._update_footer()

    def __del__(self):
        urwid.disconnect_signal(self._model, self._model.Signals.ROWS_LOADED, self.refresh)
        urwid.disconnect_signal(self._body, self._body.KEYPRESS, self._on_body_keypress)
        self._body.clear()

    @property
    def model(self):
        return self._model

    def append_column(self, column: Column):
        self._columns.append(column)
        self._layout.append_column(column)

    def render(self, size, focus=False):
        self._widget_size = size
        return super().render(size, focus)

    def refresh(self, model):
        self._visible_columns = 0
        self._focused_row_index = 0
        self._focused_col_index = 0

        width, height = self._widget_size
        columns = self._layout.layout(self._model.rows, width)

        self._rowcount = len(self._model)
        # utils.orig_w(self._header).refresh(self._model.columns)
        self._body.clear()
        self._body.set_columns(columns)
        for row in self._model:
            self._body.add_row(row)
        # self._update_footer()
        self._scroll_rows()

    def focus_row(self, row_index):
        self._focused_row_index = row_index
        self._scroll_rows()

    def resize_col(self, col_index, increment=1):
        width = self._header.original_widget.resize(col_index, increment)
        if width is None:
            return
        self._body.update_col_width(col_index, width)
        for row in self._body.body:
            trow = row.original_widget
            trow.resize(col_index, increment)
        self._emit(self.SIGNAL_COLUMN_RESIZED, col_index, width)

    def _increment_col_index(self, offset, absolute=False):
        if absolute is False:
            new_index = self._focused_col_index + offset
        else:
            new_index = offset

        if new_index < 0:
            new_index = 0
        elif new_index < self._visible_columns - 1:
            new_index = self._visible_columns - 1

        if new_index > (len(self._columns) - 1):
            new_index = len(self._columns) - 1

        self._focused_col_index = new_index

    def _increment_row_index(self, offset, absolute=False):
        if absolute is False:
            new_index = self._focused_row_index + offset
        else:
            new_index = offset

        if new_index < 0:
            new_index = 0

        if new_index > (self._rowcount - 1):
            new_index = self._rowcount - 1

        self._focused_row_index = new_index

    def _on_body_keypress(self, emitter, size, key):
        self._widget_size = size
        if not self._rowcount:
            return
        self._detect_visible_columns_count()

        row, index = self._body.body.get_focus()
        self._focused_row_index = index

        if key == 'enter':
            self._emit(self.SIGNAL_ROW_SELECTED, self._model[index])

        command = self._input_processor.process_key(key)
        if not command:
            return

        offset = command.offset
        if offset == 'page':
            offset = size[1] - 2
        if command.direction == Direction.DOWN:
            self._scroll_down(offset)
        elif command.direction == Direction.UP:
            self._scroll_up(offset)
        elif command.direction == Direction.LEFT:
            self._scroll_left(offset)
        elif command.direction == Direction.RIGHT:
            self._scroll_right(offset)

        # self._update_footer()

    def _update_footer(self):
        rowcount = self._rowcount
        cols_count = len(self._columns)

        row_index = self._focused_row_index

        status = u'[{0}/{1}:{2}]'.format(row_index + 1, rowcount, cols_count)

        self._footer.original_widget.set_text(status)

    def _detect_visible_columns_count(self):
        focused_row = self._body.focused_row
        column_widths = focused_row.column_widths(self._widget_size)
        visible_columns = 0
        for width in column_widths:
            if width > 0:
                visible_columns += 1
        self._visible_columns = visible_columns

    def _scroll_down(self, offset):
        self._increment_row_index(offset)
        self._scroll_rows()

    def _scroll_up(self, offset):
        self._increment_row_index(-1 * offset)
        self._scroll_rows()

    def _scroll_left(self, offset):
        if self._focused_col_index < self._visible_columns - 1:
            self._focused_col_index = self._visible_columns - 1
        else:
            self._increment_col_index(-1 * offset)
        self._scroll_columns()

    def _scroll_right(self, offset):
        if self._focused_col_index == 0:
            self._increment_col_index(self._visible_columns - 1 + offset, absolute=True)
        else:
            self._increment_col_index(1 * offset)
        self._scroll_columns()

    def _scroll_columns(self):
        for row in self._body.body:
            row.original_widget.focus_position = self._focused_col_index
        # self._header.original_widget.focus_position = self._focused_col_index

    def _scroll_rows(self):
        if self._focused_row_index >= len(self._model):
            return
        self._body.set_focus(self._focused_row_index)
        # Enforce the column focus because sometimes it resets to 0 and screws up
        # the rendering
        self._scroll_columns()
