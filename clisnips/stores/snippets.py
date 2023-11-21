import contextlib
import enum
import logging
from collections.abc import Callable
from typing import Any, TypedDict, TypeVar

from observ import reactive, watch

from clisnips.database import NewSnippet, Snippet, SortColumn, SortOrder
from clisnips.database.search_pager import SearchPager, SearchSyntaxError
from clisnips.database.snippets_db import SnippetsDatabase
from clisnips.utils.clock import Clock

Watched = TypeVar('Watched')


class ListLayout(enum.StrEnum):
    LIST = enum.auto()
    TABLE = enum.auto()


class QueryState(enum.Enum):
    VALID = enum.auto()
    INVALID = enum.auto()


class State(TypedDict):
    viewport: tuple[int, int]
    search_query: str
    query_state: QueryState
    snippet_ids: list[int]
    snippets_by_id: dict[int, Snippet]
    total_rows: int
    current_page: int
    page_count: int
    page_size: int
    sort_by: SortColumn
    sort_order: SortOrder
    list_layout: ListLayout


class SnippetsStore:
    def __init__(
        self,
        initial_state: State,
        db: SnippetsDatabase,
        pager: SearchPager,
        clock: Clock,
    ):
        self._state = reactive(initial_state)
        self._db = db
        self._pager = pager
        self._pager.set_sort_column(initial_state['sort_by'], initial_state['sort_order'])
        self._pager.page_size = initial_state['page_size']
        self._clock = clock
        self._fetch_list('')

    @staticmethod
    def default_state() -> State:
        return {
            'viewport': (0, 0),
            'search_query': '',
            'query_state': QueryState.VALID,
            'snippet_ids': [],
            'snippets_by_id': {},
            'total_rows': 0,
            'current_page': 1,
            'page_count': 1,
            'page_size': 25,
            'sort_by': SortColumn.RANKING,
            'sort_order': SortOrder.ASC,
            'list_layout': ListLayout.LIST,
        }

    @property
    def state(self) -> State:
        return self._state

    def watch(
        self,
        expr: Callable[[State], Watched],
        on_change: Callable[[Watched], Any],
        sync: bool = False,
        deep: bool = False,
        immediate: bool = False,
    ):
        return watch(
            fn=lambda: expr(self._state),
            callback=on_change,
            sync=sync,
            deep=deep,
            immediate=immediate,
        )

    def change_viewport(self, width: int, height: int):
        # logging.getLogger(__name__).debug('viewport=%r', (width, height))
        self._state['viewport'] = (width, height)

    def change_layout(self, layout: ListLayout):
        logging.getLogger(__name__).debug('layout=%r', layout)
        self._state['list_layout'] = layout

    def fetch_snippet(self, rowid: int) -> Snippet:
        return self._db.get(rowid)

    def use_snippet(self, rowid: int):
        # If this is called, the app is about to exit
        # so we don't need to update the state
        self._db.use_snippet(rowid, self._clock.now())

    def create_snippet(self, snippet: NewSnippet):
        rowid = self._db.insert(snippet)
        with self._handle_syntax_error():
            self._pager.count()
        # TODO: make it so we don't need to refetch the whole thing
        snippet = self._db.get(rowid)
        self._state['snippets_by_id'][rowid] = snippet
        self._state['snippet_ids'].insert(0, rowid)

    def update_snippet(self, snippet: Snippet):
        self._db.update(snippet)
        self._state['snippets_by_id'][snippet['id']] = snippet

    def delete_snippet(self, rowid: int):
        self._db.delete(rowid)
        self._state['snippet_ids'].remove(rowid)
        del self._state['snippets_by_id'][rowid]
        with self._handle_syntax_error():
            self._pager.count()

    def change_search_query(self, search_query: str):
        self._state['search_query'] = search_query
        self._fetch_list(search_query)

    def request_first_page(self):
        # TODO: skip loading if we don't need to paginate
        with self._handle_syntax_error():
            rows = self._pager.first()
            self._load_result_set(rows)

    def request_next_page(self):
        with self._handle_syntax_error():
            rows = self._pager.next()
            self._load_result_set(rows)

    def request_previous_page(self):
        with self._handle_syntax_error():
            rows = self._pager.previous()
            self._load_result_set(rows)

    def request_last_page(self):
        with self._handle_syntax_error():
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
        with self._handle_syntax_error():
            rows = self._pager.list() if not search_query else self._pager.search(search_query)
            self._load_result_set(rows)

    def _load_result_set(self, rows: list[Snippet]):
        by_id = {r['id']: r for r in rows}
        ids = list(by_id.keys())
        self._state['snippets_by_id'] = by_id
        self._state['snippet_ids'] = ids
        self._update_pager_infos()

    def _update_pager_infos(self):
        self._state['total_rows'] = self._pager.total_rows
        self._state['page_count'] = self._pager.page_count
        self._state['current_page'] = self._pager.current_page

    @contextlib.contextmanager
    def _handle_syntax_error(self):
        try:
            yield
        except SearchSyntaxError:
            self._state['query_state'] = QueryState.INVALID
        else:
            self._state['query_state'] = QueryState.VALID
