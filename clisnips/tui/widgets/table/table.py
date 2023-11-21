import urwid

from clisnips.tui.layouts.table import LayoutColumn, TableLayout
from clisnips.tui.widgets.utils import original_widget

from .body import Body
from .input_processor import InputProcessor
from .row import Row
from .store import TableStore


class Table(urwid.Frame):
    SIGNAL_ROW_SELECTED = 'row-selected'
    SIGNAL_COLUMN_RESIZED = 'column_resized'
    SIGNALS = [SIGNAL_ROW_SELECTED, SIGNAL_COLUMN_RESIZED]

    def __init__(self, model: TableStore):
        self._model = model
        self._columns = []
        self._layout = TableLayout()
        self._rowcount = len(self._model)
        # self._header = Header(self._model.columns)
        self._body = Body()
        urwid.connect_signal(self._body, 'keypress', self._on_body_keypress)

        self._footer = urwid.Text('')

        self._widget_size = (0, 0)
        self._visible_columns = 0
        self._focused_row_index = 0
        self._focused_col_index = 0
        self._input_processor = InputProcessor()

        urwid.connect_signal(model, model.Signals.ROWS_LOADED, lambda *x: self.refresh())
        urwid.connect_signal(model, model.Signals.ROW_INSERTED, self._on_row_inserted)
        urwid.connect_signal(model, model.Signals.ROW_DELETED, self._on_row_deleted)
        urwid.connect_signal(model, model.Signals.ROW_UPDATED, self._on_row_updated)

        super().__init__(
            self._body,
            # urwid.AttrMap(self._header, 'thead'),
            # urwid.AttrMap(self._footer, 'tfoot')
        )
        urwid.register_signal(self.__class__, self.SIGNALS)

    def append_column(self, column: LayoutColumn):
        self._columns.append(column)
        self._layout.append_column(column)

    def get_selected(self):
        index = self._focused_row_index
        try:
            return self._model[index]
        except IndexError:
            return None

    def render(self, size, focus=False):
        if size != self._widget_size:
            self._widget_size = size
            self.refresh()
        return super().render(size, focus)

    def refresh(self, *args):
        self._visible_columns = 0
        self._focused_row_index = 0
        self._focused_col_index = 0

        width, height = self._widget_size
        self._layout.layout(self._model.rows, width)

        self._body.clear()
        col_attr = self._layout.row_focus_attr_map
        for row_index, layout_row in enumerate(self._layout):
            row = urwid.AttrMap(Row(layout_row), 'table-row', col_attr)
            self._body.append(row)

        self._scroll_rows()

    def focus_row(self, row_index):
        self._focused_row_index = row_index
        self._scroll_rows()

    def _on_row_inserted(self, model, index, row):
        self.refresh()
        self.focus_row(index)

    def _on_row_deleted(self, model, index):
        index = self._focused_row_index
        self.refresh()
        row_count = len(self._model)
        if not row_count:
            return
        if index >= row_count:
            index = row_count - 1
        self.focus_row(index)

    def _on_row_updated(self, model, index, row):
        index = self._focused_row_index
        self.refresh()
        self.focus_row(index)

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

    #
    # def _increment_row_index(self, offset, absolute=False):
    #     if absolute is False:
    #         new_index = self._focused_row_index + offset
    #     else:
    #         new_index = offset
    #
    #     if new_index < 0:
    #         new_index = 0
    #
    #     if new_index > (self._rowcount - 1):
    #         new_index = self._rowcount - 1
    #
    #     self._focused_row_index = new_index

    def _on_body_keypress(self, emitter, size, key):
        self._widget_size = size
        if not len(self._model):
            return
        self._detect_visible_columns_count()

        row, index = self._body.body.get_focus()
        self._focused_row_index = index

        if key == 'enter':
            self._emit(self.SIGNAL_ROW_SELECTED, self._model[index])
            return
        # if key == 'left':
        #     self._scroll_left(1)
        #     return
        # if key == 'right':
        #     self._scroll_right(1)
        #     return
        return key
        # command = self._input_processor.process_key(key)
        # if not command:
        #     return
        #
        # offset = command.offset
        # if offset == 'page':
        #     offset = size[1] - 2
        # if command.direction == Direction.LEFT:
        #     self._scroll_left(offset)
        # elif command.direction == Direction.RIGHT:
        #     self._scroll_right(offset)

    def _detect_visible_columns_count(self):
        focused_row = self._body.focused_row
        column_widths = focused_row.column_widths(self._widget_size)
        visible_columns = 0
        for width in column_widths:
            if width > 0:
                visible_columns += 1
        self._visible_columns = visible_columns

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
        for row in self._body:
            original_widget(row).focus_position = self._focused_col_index

    def _scroll_rows(self):
        if self._focused_row_index >= len(self._model):
            return
        self._body.set_focus(self._focused_row_index)
        # Enforce the column focus because sometimes it resets to 0 and screws up the rendering
        self._scroll_columns()
