import sqlite3
from typing import Union

from .pager import Pager
from .scrolling_pager import ScrollingPager
from .snippets_db import SnippetsDatabase


SearchPagerType = Union[Pager, 'SearchPager']


class SearchSyntaxError(RuntimeError):
    pass


class SearchPager:

    def __init__(self, db: SnippetsDatabase, page_size: int):
        self._page_size = page_size
        self._list_pager = ScrollingPager(db.connection, page_size)
        self._list_pager.set_query(db.get_listing_query())
        self._list_pager.set_count_query(db.get_listing_count_query())

        self._search_pager = ScrollingPager(db.connection, page_size)
        self._search_pager.set_query(db.get_search_query())
        self._search_pager.set_count_query(db.get_search_count_query())

        self._is_searching = False
        self._current_pager = self._list_pager

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
        try:
            self.execute(params, params)
        except sqlite3.OperationalError as err:
            # HACK: If only there was a better way ...
            if err.args and str(err.args[0]).startswith('fts5: syntax error'):
                raise SearchSyntaxError(term)
            else:
                raise err
        else:
            return self.first()

    def list(self):
        self._is_searching = False
        self._current_pager = self._list_pager
        return self.execute().first()

    def set_sort_column(self, column: str):
        self.set_sort_columns([
            (column, 'DESC'),
            ('id', 'ASC', True)
        ])

    def set_sort_columns(self, columns):
        self._list_pager.set_sort_columns(columns)
        self._search_pager.set_sort_columns(columns)

    def set_page_size(self, size: int):
        self._page_size = size
        self._list_pager.set_page_size(size)
        self._search_pager.set_page_size(size)

    def execute(self, params=(), count_params=()):
        self._current_pager.execute(params, count_params)
        return self

    def __getattr__(self, attr):
        return getattr(self._current_pager, attr)

    def __len__(self):
        return len(self._current_pager)
