import urwid

from ..logging import logger
from ..widgets.search_entry import SearchEntry
from ..widgets.table.column import Column
from ..widgets.table.store import Store as ListStore
from ..widgets.table.table import Table


class SnippetListView(urwid.Frame):

    signals = ['search-changed', 'snippet-selected']

    def __init__(self, store: ListStore):
        self.search_entry = SearchEntry()
        self.snippet_list = Table(store)
        self.snippet_list.append_column(Column('cmd'))
        self.snippet_list.append_column(Column('title'))
        self.snippet_list.append_column(Column('tag'))

        urwid.connect_signal(self.search_entry, 'change', self._on_search_term_changed)
        urwid.connect_signal(self.snippet_list, 'row-selected', self._on_snippet_list_row_selected)

        super().__init__(self.snippet_list, header=self.search_entry, focus_part='header')

    def keypress(self, size, key):
        key = super().keypress(size, key)
        if key in ('tab', 'shift tab'):
            if self.focus_position == 'header':
                self.focus_position = 'body'
            else:
                self.focus_position = 'header'
        if key == 'down' and self.focus_position == 'header':
            self.focus_position = 'body'
        if key == 'up' and self.focus_position == 'body':
            self.focus_position = 'header'

    def _on_search_term_changed(self, entry, text):
        self._emit('search-changed', text)

    def _on_snippet_list_row_selected(self, table, row):
        self._emit('snippet-selected', row)
