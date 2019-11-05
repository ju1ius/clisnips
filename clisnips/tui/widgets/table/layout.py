import math
import re
import textwrap
from math import floor
from typing import Iterable, Tuple

from .column import Column

_WORD_SPLIT_RX = re.compile(r'\W+', re.UNICODE)


class TableLayout:

    def __init__(self):
        self._columns = []
        self._rows = []

    def __len__(self):
        return len(self._rows)

    def __iter__(self):
        yield from self._rows

    @property
    def row_focus_attr_map(self):
        attr_map = {None: 'table-row:focused'}
        attr_map.update({
            f'table-column:{col.index}': f'table-column:{col.index}:focused'
            for col in self._columns
        })
        return attr_map

    def append_column(self, column: Column):
        self._columns.append(column)

    def layout(self, rows: Iterable, available_width: int):
        if not available_width:
            available_width = math.inf
        self._compute_content_sizes(rows)
        self._distribute_width(available_width)
        self._distribute_height(rows)

    def _compute_content_sizes(self, data_rows):
        self._rows = []
        for data_row in data_rows:
            layout_row = LayoutRow(self._columns, data_row)
            for column in self._columns:
                value = data_row[column.index]
                content_width, content_height = self._compute_cell_content_size(value)
                column.content_width = max(column.content_width, content_width)
                layout_row.content_height = max(layout_row.content_height, content_height)
                layout_row.computed_height = layout_row.content_height
                min_content_width = self._compute_cell_min_content_width(value)
                column.min_content_width = max(column.min_content_width, min_content_width)
            self._rows.append(layout_row)
        for column in self._columns:
            column.compute_width()
            column.compute_min_width()
            if column.computed_width > column.max_width:
                column.computed_width = column.max_width
            if column.computed_width < column.min_width:
                column.computed_width = column.min_width

    def _distribute_width(self, available_width):
        total_width = self._compute_total_width()
        # adjust if short of space
        if total_width > available_width:
            # share the available space between resizeable columns
            fixed_width = self._compute_total_fixed_columns_width()
            resizable_width = max(0, available_width - fixed_width)
            resizable_columns = list(self._get_resizable_columns())
            for column in resizable_columns:
                column.computed_width = floor(resizable_width / len(resizable_columns))

            # at this point, the computed_width should never end up bigger than the content_width
            salvaged_space = 0

            grown_columns = (c for c in self._columns if c.computed_width > c.content_width)
            for column in grown_columns:
                current_width = column.computed_width
                column.compute_width()
                salvaged_space += current_width - column.computed_width

            shrunken_columns = [c for c in self._columns if c.computed_width < c.content_width]
            for column in shrunken_columns:
                column.computed_width += floor(salvaged_space / len(shrunken_columns))

            # bail out if we still don't fit within max_width

    def _distribute_height(self, data_rows):
        for index, data_row in enumerate(data_rows):
            layout_row = self._rows[index]
            for column in self._columns:
                # if column.computed_width >= column.content_width:
                #     continue
                # if not column.word_wrap:
                #     continue
                value = data_row[column.index]
                lines = textwrap.wrap(value, column.computed_width - column.padding.length)
                layout_row.computed_height = max(layout_row.computed_height, len(lines))
                layout_row[column] = '\n'.join(lines)

    def _compute_total_width(self) -> int:
        return sum(col.computed_width for col in self._columns)

    def _compute_total_fixed_columns_width(self) -> int:
        return sum(col.computed_width for col in self._get_fixed_columns())

    def _get_fixed_columns(self):
        return (col for col in self._columns if col.is_fixed)

    def _get_resizable_columns(self):
        return (col for col in self._columns if col.is_resizable)

    @staticmethod
    def _compute_cell_content_size(value) -> Tuple[int, int]:
        value = str(value)
        if not value:
            return 0, 0
        lines = value.splitlines()
        longest_line = max(lines, key=len)
        return len(longest_line), len(lines)

    @staticmethod
    def _compute_cell_min_content_width(value) -> int:
        value = str(value)
        if not value:
            return 0
        words = _WORD_SPLIT_RX.split(value)
        longest_word = max(words, key=len)
        return len(longest_word)


class LayoutRow:

    def __init__(self, columns, data):
        self._columns = columns
        self._data = dict(data)
        self.content_height = 0
        self.min_content_height = 1
        self.computed_height = 0

    def __len__(self):
        return len(self._columns)

    def __iter__(self):
        for column in self._columns:
            yield column, self._data[column.index]

    def __setitem__(self, column, value):
        if not isinstance(column, Column):
            raise TypeError(f'Expected <Column>, got {type(column).__name__}')
        self._data[column.index] = value

    def __getitem__(self, column):
        if not isinstance(column, Column):
            raise TypeError(f'Expected <Column>, got {type(column).__name__}')
        return self._data[column.index]
