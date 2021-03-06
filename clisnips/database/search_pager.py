import sqlite3
from contextlib import contextmanager
from typing import Iterable, Union

from .pager import Pager
from .scrolling_pager import ScrollingPager, SortColumnDefinition
from .snippets_db import SnippetsDatabase

SearchPagerType = Union[Pager, 'SearchPager']


class SearchSyntaxError(RuntimeError):
    pass


class SearchPager:

    def __init__(self, db: SnippetsDatabase,
                 sort_column: SortColumnDefinition = ('ranking', 'DESC'),
                 page_size: int = 50):
        self._page_size = page_size
        self._list_pager = ScrollingPager(db.connection, page_size)
        self._list_pager.set_query(db.get_listing_query())
        self._list_pager.set_count_query(db.get_listing_count_query())

        self._search_pager = ScrollingPager(db.connection, page_size)
        self._search_pager.set_query(db.get_search_query())
        self._search_pager.set_count_query(db.get_search_count_query())

        self._is_searching = False
        self._current_pager = self._list_pager
        self.set_sort_column(*sort_column)

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

    def set_sort_column(self, column: str, order: str = 'DESC'):
        self.set_sort_columns([
            (column, order),
            ('id', 'ASC', True)
        ])

    def set_sort_columns(self, columns: Iterable[SortColumnDefinition]):
        self._list_pager.set_sort_columns(columns)
        self._search_pager.set_sort_columns(columns)

    def set_page_size(self, size: int):
        self._page_size = size
        self._list_pager.set_page_size(size)
        self._search_pager.set_page_size(size)

    def execute(self, params=(), count_params=()):
        with self._convert_exceptions():
            self._current_pager.execute(params, count_params)
        return self

    def count(self):
        with self._convert_exceptions():
            self._current_pager.count()

    def __getattr__(self, attr):
        return getattr(self._current_pager, attr)

    def __len__(self):
        return len(self._current_pager)

    @contextmanager
    def _convert_exceptions(self):
        try:
            yield
        except sqlite3.OperationalError as err:
            if self._is_searching and len(err.args):
                msg = str(err.args[0])
                if msg.startswith('fts5: syntax error') or msg.startswith('no such column'):
                    raise SearchSyntaxError(msg)
            raise err
