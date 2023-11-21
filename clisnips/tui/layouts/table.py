"""
Very simple text table layout algorithm.

TODO: https://drafts.csswg.org/css-tables-3
"""

import re
import sys
import textwrap
from collections.abc import Hashable, Iterable, Mapping
from math import floor
from typing import Any, Generic, TypeVar

T = TypeVar('T', bound=Mapping)


class InlinePadding:
    def __init__(self, start: int = 0, end: int = 0):
        self.start = start
        self.end = end
        self.length = start + end

    def __len__(self):
        return self.length


class LayoutColumn:
    """
    Represents a table column
    """

    def __init__(
        self,
        key: Hashable,
        width: int | None = None,
        min_width: int = 0,
        max_width: int = sys.maxsize,
        padding: tuple[int, int] = (0, 0),
        wrap: bool = False,
    ):
        self.key = key
        self.width = width
        self.min_width = min_width
        self.max_width = max_width
        self.word_wrap = wrap
        self.padding = InlinePadding(*padding)
        #
        self.wrappable = True
        self.content_width: int = 0
        self.min_content_width: int = 0
        self.computed_width: int = 0

    def invalidate(self):
        self.content_width: int = 0
        self.min_content_width: int = 0
        self.computed_width: int = 0

    @property
    def is_resizable(self) -> bool:
        return not self.is_fixed

    @property
    def is_fixed(self) -> bool:
        return bool(self.width) or not self.word_wrap or not self.wrappable

    def compute_width(self):
        self.computed_width = self.width or (self.content_width + self.padding.length)

    def compute_min_width(self):
        self.min_width = self.min_content_width + self.padding.length

    def __repr__(self):
        return f'<Column[{self.key}] ({self.computed_width})>'


class LayoutRow(Generic[T]):
    def __init__(self, columns: list[LayoutColumn], data: T):
        self._columns = columns
        self._data = dict(data)
        #
        self.content_height = 0
        self.min_content_height = 1
        self.computed_height = 0

    def invalidate(self):
        self.content_height: int = 0
        self.min_content_height: int = 0
        self.computed_height: int = 0

    def __len__(self):
        return len(self._columns)

    def __iter__(self):
        for column in self._columns:
            yield column, self._data[column.key]

    def __setitem__(self, column: LayoutColumn, value: Any):
        self._data[column.key] = value

    def __getitem__(self, column: LayoutColumn):
        return self._data[column.key]

    def __repr__(self) -> str:
        return f'<Row(height={self.computed_height}, data={self._data!r})>'


_WORD_SPLIT_RX = re.compile(r'\W+', re.UNICODE)


class TableLayout(Generic[T]):
    def __init__(self):
        self._columns: list[LayoutColumn] = []
        self._rows: list[LayoutRow[T]] = []

    def __len__(self):
        return len(self._rows)

    def __iter__(self):
        yield from self._rows

    @property
    def row_focus_attr_map(self):
        attr_map: dict[str | None, str] = {None: 'table-row:focused'}
        attr_map.update({f'table-column:{col.key}': f'table-column:{col.key}:focused' for col in self._columns})
        return attr_map

    def append_column(self, column: LayoutColumn):
        self._columns.append(column)

    def invalidate(self):
        for col in self._columns:
            col.invalidate()

    def layout(self, rows: Iterable[T], available_width: int):
        if not available_width:
            available_width = sys.maxsize
        self._compute_content_sizes(rows)
        self._distribute_width(available_width)
        self._distribute_height(rows)

    def _compute_content_sizes(self, data_rows: Iterable[T]):
        self._rows = []
        for data_row in data_rows:
            layout_row = LayoutRow(self._columns, data_row)
            for column in self._columns:
                value = data_row[column.key]
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

    def _distribute_height(self, data_rows: Iterable[T]):
        for index, data_row in enumerate(data_rows):
            layout_row = self._rows[index]
            for column in self._columns:
                # if column.computed_width >= column.content_width:
                #     continue
                # if not column.word_wrap:
                #     continue
                value = data_row[column.key]
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
    def _compute_cell_content_size(value) -> tuple[int, int]:
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
