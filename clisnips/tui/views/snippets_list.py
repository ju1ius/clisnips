import urwid

from ..models.snippets import SnippetsModel
from ..view import View
from ..widgets.search_entry import SearchEntry
from ..widgets.show_snippet_dialog import ShowSnippetDialog
from ..widgets.snippets_list_footer import SnippetListFooter
from ..widgets.sort_dialog import SortDialog
from ..widgets.table.column import Column
from ..widgets.table.store import Store as ListStore
from ..widgets.table.table import Table


class SnippetListView(View):

    signals = [
        'search-changed',
        'snippet-selected',
        'sort-column-selected',
        'sort-order-selected',
        'page-requested',
    ]

    def __init__(self, model: SnippetsModel):

        self._model = model
        self._model.connect(model.Signals.ROWS_LOADED, self._on_model_rows_loaded)

        self.search_entry = SearchEntry()
        urwid.connect_signal(self.search_entry, 'change', self._on_search_term_changed)

        self._list_store = ListStore()
        self.snippet_list = Table(self._list_store)
        self.snippet_list.append_column(Column('cmd'))
        self.snippet_list.append_column(Column('title'))
        self.snippet_list.append_column(Column('tag'))
        urwid.connect_signal(self.snippet_list, 'row-selected', self._on_snippet_list_row_selected)

        self._footer = SnippetListFooter()

        frame = urwid.Frame(self.snippet_list, header=self.search_entry, footer=self._footer, focus_part='header')
        super().__init__(frame)

    def get_search_text(self):
        return self.search_entry.get_search_text()

    def _open_sort_dialog(self):
        dialog = SortDialog(self, self._model)
        urwid.connect_signal(dialog, 'sort-changed', self._on_sort_column_selected)
        self.open_dialog(dialog, title='Sort Options', width=35, height=12)

    def _open_show_dialog(self):
        row = self.snippet_list.get_selected()
        if not row:
            return
        snippet = self._model.get(row['id'])
        dialog = ShowSnippetDialog(self, snippet)
        self.open_dialog(dialog, title='Show snippet')

    def _on_model_rows_loaded(self, model: SnippetsModel, rows):
        self._list_store.load(rows)
        self._footer.set_pager_infos(model.current_page, model.page_count, model.row_count)

    def keypress(self, size, key):
        if key == '?':
            return
        if key == 'f2':
            self._open_sort_dialog()
            return
        key = super().keypress(size, key)
        if key in ('tab', 'shift tab'):
            if self.view.focus_position == 'header':
                self.view.focus_position = 'body'
            else:
                self.view.focus_position = 'header'
            return
        if key == 'down' and self.view.focus_position == 'header':
            self.view.focus_position = 'body'
            return
        if key == 'up' and self.view.focus_position == 'body':
            self.view.focus_position = 'header'
            return
        if key == 'n':
            self._emit('page-requested', 'next')
            return
        if key == 'p':
            self._emit('page-requested', 'previous')
            return
        if key == 'f':
            self._emit('page-requested', 'first')
            return
        if key == 'l':
            self._emit('page-requested', 'last')
            return
        if key == 's':
            self._open_show_dialog()
            return

    def _on_search_term_changed(self, entry, text):
        self._emit('search-changed', text)

    def _on_snippet_list_row_selected(self, table, row):
        self._emit('snippet-selected', row)

    def _on_sort_column_selected(self, dialog, column, order):
        self._emit('sort-column-selected', column, order)
