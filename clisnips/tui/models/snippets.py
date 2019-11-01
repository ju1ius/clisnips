import enum

import urwid

from ...database.pager import Pager
from ...database.search_pager import SearchPager, SearchPagerType, SearchSyntaxError
from ...database.snippets_db import SnippetsDatabase


class SnippetsModel:

    class Signals(enum.Enum):
        ROWS_LOADED = 'rows-loaded'
        ROW_CREATED = 'row-created'
        ROW_DELETED = 'row-deleted'
        ROW_UPDATED = 'row-updated'

    def __init__(self, db: SnippetsDatabase):
        self._db = db
        self._pager: SearchPagerType = SearchPager(db, page_size=50)
        self._pager.set_sort_column('ranking', 'DESC')

        urwid.register_signal(self.__class__, list(self.Signals))

    def connect(self, signal, callback, weak_args=None, user_args=None):
        urwid.connect_signal(self, signal, callback, weak_args=weak_args, user_args=user_args)

    @property
    def must_paginate(self):
        return self._pager.must_paginate

    @property
    def page_count(self):
        return self._pager.page_count

    @property
    def current_page(self):
        return self._pager.current_page

    @property
    def is_first_page(self):
        return self._pager.is_first_page

    @property
    def is_last_page(self):
        return self._pager.is_last_page

    @property
    def row_count(self):
        return self._pager.total_rows

    @property
    def is_searching(self):
        return self._pager.is_searching

    @property
    def sort_column(self):
        column, order = self._pager.get_sort_columns()[0]
        return column, 'ASC' if order is Pager.SORT_ASC else 'DESC'

    def set_sort_column(self, column, order='DESC'):
        self._pager.set_sort_column(column, order)

    def get(self, snippet_id):
        return self._db.get(snippet_id)

    def create(self, snippet):
        rowid = self._db.insert(snippet)
        self._pager.count()
        snippet = self._db.get(rowid)
        self._emit(self.Signals.ROW_CREATED, snippet)

    def update(self, snippet):
        self._db.update(snippet)
        self._emit(self.Signals.ROW_UPDATED, snippet['id'], snippet)

    def delete(self, rowid):
        self._db.delete(rowid)
        self._pager.count()
        self._emit(self.Signals.ROW_DELETED, rowid)

    def search(self, term: str):
        try:
            rows = self._pager.search(term)
        except SearchSyntaxError:
            return
        self._load(rows)

    def list(self):
        rows = self._pager.list()
        self._load(rows)

    def first_page(self):
        rows = self._pager.first()
        self._load(rows)

    def next_page(self):
        rows = self._pager.next()
        self._load(rows)

    def previous_page(self):
        rows = self._pager.previous()
        self._load(rows)

    def last_page(self):
        rows = self._pager.last()
        self._load(rows)

    def _load(self, rows):
        self._emit(self.Signals.ROWS_LOADED, rows)

    def _emit(self, signal, *args):
        urwid.emit_signal(self, signal, self, *args)
