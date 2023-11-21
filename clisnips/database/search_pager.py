from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from contextlib import contextmanager
from typing import TYPE_CHECKING, Self

from . import Snippet, SortColumn, SortOrder
from .scrolling_pager import ScrollingPager, SortColumnDefinition
from .snippets_db import QueryParameters, SnippetsDatabase


class SearchSyntaxError(RuntimeError):
    pass


# There's no way to declare a proxy type with the current type-checkers
# so we extend
class SearchPager(ScrollingPager[Snippet] if TYPE_CHECKING else object):
    def __init__(
        self,
        db: SnippetsDatabase,
        sort_column: tuple[SortColumn, SortOrder] = (SortColumn.RANKING, SortOrder.DESC),
        page_size: int = 50,
    ):
        self._page_size = page_size
        self._list_pager: ScrollingPager[Snippet] = ScrollingPager(db.connection, page_size)
        self._list_pager.set_query(db.get_listing_query())
        self._list_pager.set_count_query(db.get_listing_count_query())

        self._search_pager: ScrollingPager[Snippet] = ScrollingPager(db.connection, page_size)
        self._search_pager.set_query(db.get_search_query())
        self._search_pager.set_count_query(db.get_search_count_query())

        self._is_searching = False
        self._current_pager = self._list_pager
        self.set_sort_column(*sort_column)

    def __getattr__(self, attr: str):
        return getattr(self._current_pager, attr)

    @property
    def is_searching(self) -> bool:
        return self._is_searching

    @property
    def page_size(self) -> int:
        return self._page_size

    @page_size.setter
    def page_size(self, size: int):
        self.set_page_size(size)

    def search(self, term: str):
        self._is_searching = True
        self._current_pager = self._search_pager
        params = {'term': term}
        self.execute(params, params)
        return self.first()

    def list(self):
        self._is_searching = False
        self._current_pager = self._list_pager
        return self.execute().first()

    def set_sort_column(self, column: SortColumn, order: SortOrder = SortOrder.DESC):
        self.set_sort_columns(
            (
                (column, order),
                ('id', SortOrder.ASC, True),
            )
        )

    def set_sort_columns(self, columns: Iterable[SortColumnDefinition]):
        self._list_pager.set_sort_columns(columns)
        self._search_pager.set_sort_columns(columns)

    def set_page_size(self, size: int):
        self._page_size = size
        self._list_pager.set_page_size(size)
        self._search_pager.set_page_size(size)

    def execute(self, params: QueryParameters = (), count_params: QueryParameters = ()) -> Self:
        with self._convert_exceptions():
            self._current_pager.execute(params, count_params)
        return self

    def count(self):
        with self._convert_exceptions():
            self._current_pager.count()

    def __len__(self):
        return len(self._current_pager)

    @contextmanager
    def _convert_exceptions(self):
        try:
            yield
        except sqlite3.OperationalError as err:
            if self._is_searching and _is_search_syntax_error(err):
                raise SearchSyntaxError(*err.args) from err
            raise err


def _is_search_syntax_error(err: sqlite3.OperationalError) -> bool:
    if not err.args:
        return False
    msg = str(err.args[0])
    return (
        msg.startswith('fts5: syntax error')
        or msg.startswith('no such column')
        or msg.startswith('unknown special query:')
    )
