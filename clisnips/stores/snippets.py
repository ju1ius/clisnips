from contextlib import suppress
from typing import Any, Callable, TypeVar, TypedDict

from observ import reactive, watch, watch_effect

from clisnips.database import SortColumn, SortOrder
from clisnips.database.search_pager import SearchPager, SearchSyntaxError
from clisnips.database.snippets_db import Snippet, SnippetsDatabase
from clisnips.utils.clock import Clock

Watched = TypeVar("Watched")


class State(TypedDict):
    search_query: str
    snippets_by_id: dict[int, Snippet]
    total_rows: int
    current_page: int
    page_count: int
    page_size: int
    sort_by: SortColumn
    sort_order: SortOrder


DEFAULT_STATE: State = {
    'search_query': '',
    'snippets_by_id': {},
    'total_rows': 0,
    'current_page': 1,
    'page_count': 1,
    'page_size': 25,
    'sort_by': SortColumn.RANKING,
    'sort_order': SortOrder.ASC,
}


class SnippetsStore:

    def __init__(
        self,
        initial_state: State,
        db: SnippetsDatabase,
        pager: SearchPager,
        clock: Clock,
    ):
        self._state: State = reactive(initial_state)
        self._db = db
        self._pager = pager
        self._clock = clock
        self._fetch_list('')

    @property
    def state(self) -> State:
        return self._state

    def watch(
        self,
        expr: Callable[[State], Watched],
        on_change: Callable[[Watched], Any],
        sync=False,
        deep=False,
        immediate=False
    ):
        return watch(
            fn=lambda: expr(self._state),
            callback=on_change,
            sync=sync,
            deep=deep,
            immediate=immediate,
        )

    def effect(self, expr: Callable[[State], Watched], sync=False, deep=False, immediate=False):
        return watch_effect(
            fn=lambda: expr(self._state),
            sync=sync,
            deep=deep,
            immediate=immediate,
        )

    def fetch_snippet(self, rowid: int) -> Snippet:
        return self._db.get(rowid)

    def create_snippet(self, snippet: Snippet):
        rowid = self._db.insert(snippet)
        with suppress(SearchSyntaxError):
            self._pager.count()
        snippet = self._db.get(rowid)
        # TODO: insert snippet on top of the list

    def update_snippet(self, snippet: Snippet):
        self._db.update(snippet)
        self._state['snippets_by_id'][snippet['id']] = snippet

    def delete_snippet(self, rowid: int):
        self._db.delete(rowid)
        del self._state['snippets_by_id'][rowid]
        with suppress(SearchSyntaxError):
            self._pager.count()

    def change_search_query(self, search_query: str):
        self._state['search_query'] = search_query
        self._fetch_list(search_query)

    def request_first_page(self):
        # TODO: skip loading if we don't need to paginate
        with suppress(SearchSyntaxError):
            rows = self._pager.first()
        self._load_result_set(rows)

    def request_next_page(self):
        with suppress(SearchSyntaxError):
            rows = self._pager.next()
        self._load_result_set(rows)

    def request_previous_page(self):
        with suppress(SearchSyntaxError):
            rows = self._pager.previous()
        self._load_result_set(rows)

    def request_last_page(self):
        with suppress(SearchSyntaxError):
            rows = self._pager.last()
        self._load_result_set(rows)

    def change_sort_column(self, column: SortColumn):
        self._state['sort_by'] = column
        self._pager.set_sort_column(column, self._state['sort_order'])
        self._fetch_list(self._state['search_query'])

    def change_sort_order(self, order: SortOrder):
        self._state['sort_order'] = order
        self._pager.set_sort_column(self._state['sort_by'], order)
        self._fetch_list(self._state['search_query'])

    def change_page_size(self, size: int):
        self._state['page_size'] = size
        self._pager.set_page_size(size)
        self._fetch_list(self._state['search_query'])

    def _fetch_list(self, search_query: str):
        if not search_query:
            rows = self._pager.list()
        else:
            with suppress(SearchSyntaxError):
                rows = self._pager.search(search_query)
        self._load_result_set(rows)

    def _load_result_set(self, rows: list):
        self._state['snippets_by_id'] = {row['id']: row for row in rows}
        self._update_pager_infos()

    def _update_pager_infos(self):
        self._state['total_rows'] = self._pager.total_rows
        self._state['page_count'] = self._pager.page_count
        self._state['current_page'] = self._pager.current_page
