import enum
from contextlib import suppress
from typing import Any, Callable, Iterable, Tuple

import urwid

from clisnips.database import SortColumn, SortOrder
from clisnips.database.pager import Pager
from clisnips.database.search_pager import SearchPagerType, SearchSyntaxError
from clisnips.database.snippets_db import SnippetsDatabase


class SnippetsModel:

    class Signals(enum.Enum):
        ROWS_LOADED = 'rows-loaded'
        ROW_CREATED = 'row-created'
        ROW_DELETED = 'row-deleted'
        ROW_UPDATED = 'row-updated'

    def __init__(self, db: SnippetsDatabase, pager: SearchPagerType):
        self._db = db
        self._pager = pager
        urwid.register_signal(self.__class__, list(self.Signals))

    def get_database(self) -> SnippetsDatabase:
        return self._db

    def connect(
        self,
        signal: Signals,
        callback: Callable[..., Any],
        weak_args: Iterable = (),
        user_args: Iterable = (),
    ):
        urwid.connect_signal(self, signal, callback, weak_args=weak_args, user_args=user_args)

    @property
    def must_paginate(self) -> bool:
        return self._pager.must_paginate

    @property
    def page_count(self) -> int:
        return self._pager.page_count

    @property
    def page_size(self) -> int:
        return self._pager.page_size

    def set_page_size(self, size: int):
        self._pager.set_page_size(size)

    @property
    def current_page(self) -> int:
        return self._pager.current_page

    @property
    def is_first_page(self) -> bool:
        return self._pager.is_first_page

    @property
    def is_last_page(self) -> bool:
        return self._pager.is_last_page

    @property
    def row_count(self) -> int:
        return self._pager.total_rows

    @property
    def is_searching(self) -> bool:
        return self._pager.is_searching

    @property
    def sort_column(self) -> Tuple[str, SortOrder]:
        column, order, *_ = self._pager.get_sort_columns()[0]
        return column, order

    def set_sort_column(self, column: SortColumn, order=SortOrder.DESC):
        self._pager.set_sort_column(column, order)

    def get(self, snippet_id):
        return self._db.get(snippet_id)

    def create(self, snippet):
        rowid = self._db.insert(snippet)
        with suppress(SearchSyntaxError):
            self._pager.count()
        snippet = self._db.get(rowid)
        self._emit(self.Signals.ROW_CREATED, snippet)

    def update(self, snippet):
        self._db.update(snippet)
        self._emit(self.Signals.ROW_UPDATED, snippet['id'], snippet)

    def delete(self, rowid):
        self._db.delete(rowid)
        with suppress(SearchSyntaxError):
            self._pager.count()
        self._emit(self.Signals.ROW_DELETED, rowid)

    def search(self, term: str):
        with suppress(SearchSyntaxError):
            rows = self._pager.search(term)
            self._load(rows)

    def list(self):
        rows = self._pager.list()
        self._load(rows)

    def first_page(self):
        with suppress(SearchSyntaxError):
            rows = self._pager.first()
            self._load(rows)

    def next_page(self):
        with suppress(SearchSyntaxError):
            rows = self._pager.next()
            self._load(rows)

    def previous_page(self):
        with suppress(SearchSyntaxError):
            rows = self._pager.previous()
            self._load(rows)

    def last_page(self):
        with suppress(SearchSyntaxError):
            rows = self._pager.last()
            self._load(rows)

    def _load(self, rows):
        self._emit(self.Signals.ROWS_LOADED, rows)

    def _emit(self, signal, *args):
        urwid.emit_signal(self, signal, self, *args)
