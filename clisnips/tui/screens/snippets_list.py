import urwid

from ..screen import Screen
from ..views.snippets_list import SnippetListView
from ..widgets.table.store import Store as ListStore
from ...database.search_pager import SearchPager, SearchSyntaxError
from ...database.snippets_db import SnippetsDatabase


class SnippetsListScreen(Screen):

    def __init__(self, db: SnippetsDatabase):
        super().__init__(['snippet-applied'])

        self._pager = SearchPager(db, page_size=50)
        self._pager.set_sort_column('ranking')
        self._store = ListStore()

        self.view = SnippetListView(self._store)
        urwid.connect_signal(self.view, 'search-changed', self. _on_search_term_changed)
        urwid.connect_signal(self.view, 'snippet-selected', self._on_snippet_selected)

        self._load_snippets()

    def _load_snippets(self):
        rows = self._pager.list()
        self._store.load(rows)

    def _on_search_term_changed(self, view, text):
        if not text:
            self._load_snippets()
            return
        try:
            rows = self._pager.search(text)
        except SearchSyntaxError:
            return
        if rows:
            # TODO: is a search returned several pages and the user continue typing,
            #  and the search returns no results, then the pager's internal state is inconsistent
            #  with the ui if we don't update the store
            self._store.load(rows)

    def _on_snippet_selected(self, view, row):
        # TODO: show command dialog if needed
        urwid.emit_signal(self, 'snippet-applied', row['cmd'])
