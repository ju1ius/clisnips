import re
from math import floor
from typing import Iterable

from .column import Column

_WORD_SPLIT_RX = re.compile(r'\W+', re.UNICODE)


class TableLayout:

    def __init__(self):
        self._columns = []

    def append_column(self, column: Column):
        self._columns.append(column)

    def layout(self, rows: Iterable, available_width: int):
        self._compute_content_widths(rows)
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
        return self._columns

    def _compute_content_widths(self, rows):
        for row in rows:
            for column in self._columns:
                value = row[column.index]
                content_width = self._compute_cell_content_width(value)
                column.content_width = max(column.content_width, content_width)
                min_content_width = self._compute_cell_min_content_width(value)
                column.min_content_width = max(column.min_content_width, min_content_width)
        for column in self._columns:
            column.compute_width()
            column.compute_min_width()
            if column.computed_width > column.max_width:
                column.computed_width = column.max_width
            if column.computed_width < column.min_width:
                column.computed_width = column.min_width

    def _compute_total_width(self) -> int:
        return sum(col.computed_width for col in self._columns)

    def _compute_total_fixed_columns_width(self) -> int:
        return sum(col.computed_width for col in self._get_fixed_columns())

    def _get_fixed_columns(self):
        return (col for col in self._columns if col.is_fixed)

    def _get_resizable_columns(self):
        return (col for col in self._columns if col.is_resizable)

    @staticmethod
    def _compute_cell_content_width(value) -> int:
        value = str(value)
        longest_line = max(value.splitlines(), key=len)
        return len(longest_line)

    @staticmethod
    def _compute_cell_min_content_width(value) -> int:
        value = str(value)
        words = _WORD_SPLIT_RX.split(value)
        longest_word = max(words, key=len)
        return len(longest_word)
