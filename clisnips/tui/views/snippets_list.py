import urwid

from ..logging import logger
from ..models.snippets import SnippetsModel
from ..view import View
from ..widgets.dialogs.confirm import ConfirmDialog
from ..widgets.dialogs.edit_snippet import EditSnippetDialog
from ..widgets.dialogs.insert_snippet import InsertSnippetDialog
from ..widgets.dialogs.list_options import ListOptionsDialog
from ..widgets.dialogs.show_snippet import ShowSnippetDialog
from ..widgets.pager_infos import PagerInfos
from ..widgets.search_entry import SearchEntry
from ..widgets.snippets_list_footer import SnippetListFooter
from ..widgets.table import Column, Table, TableStore


class SnippetListView(View):

    signals = [
        'search-changed',
        'snippet-selected',
        'sort-column-selected',
        'sort-order-selected',
        'page-size-changed',
        'page-requested',
        'apply-snippet-requested',
        'create-snippet-requested',
        'delete-snippet-requested',
        'edit-snippet-requested',
    ]

    def __init__(self, model: SnippetsModel):

        self._model = model
        self._model.connect(model.Signals.ROWS_LOADED, self._on_model_rows_loaded)
        self._model.connect(model.Signals.ROW_CREATED, self._on_model_row_created)
        self._model.connect(model.Signals.ROW_DELETED, self._on_model_row_deleted)
        self._model.connect(model.Signals.ROW_UPDATED, self._on_model_row_updated)

        self.search_entry = SearchEntry('Search term: ')
        urwid.connect_signal(self.search_entry, 'change', self._on_search_term_changed)
        pager_infos = PagerInfos(model)
        header = urwid.Columns([('weight', 1, self.search_entry), ('pack', pager_infos)], dividechars=1)

        self._table_store = TableStore()
        self.snippet_list = Table(self._table_store)
        self.snippet_list.append_column(Column('cmd'))
        self.snippet_list.append_column(Column('title'))
        self.snippet_list.append_column(Column('tag'))
        urwid.connect_signal(self.snippet_list, 'row-selected', self._on_snippet_list_row_selected)

        self._footer = SnippetListFooter(model)

        frame = urwid.Frame(self.snippet_list, header=header, footer=self._footer, focus_part='header')
        super().__init__(frame)

    def get_search_text(self):
        return self.search_entry.get_search_text()

    def open_insert_snippet_dialog(self, snippet):
        dialog = InsertSnippetDialog(self, snippet)
        dialog.on_accept(lambda v: self._emit('apply-snippet-requested', v))
        self.open_dialog(dialog, title='Insert snippet')

    def _open_sort_dialog(self):
        dialog = ListOptionsDialog(self, self._model)
        urwid.connect_signal(dialog, 'sort-changed', self._on_sort_column_selected)
        urwid.connect_signal(dialog, 'page-size-changed', self._on_page_size_changed)
        self.open_dialog(dialog, title='List Options', width=35, height=14)

    def _open_show_dialog(self):
        row = self.snippet_list.get_selected()
        if not row:
            return
        snippet = self._model.get(row['id'])
        dialog = ShowSnippetDialog(self, snippet)
        self.open_dialog(dialog, title='Show snippet')

    def _open_edit_dialog(self):
        row = self.snippet_list.get_selected()
        if not row:
            return
        snippet = self._model.get(row['id'])
        dialog = EditSnippetDialog(self, snippet)
        dialog.on_accept(self._on_edit_dialog_accept)
        self.open_dialog(dialog, title='Edit snippet')

    def _open_create_dialog(self):
        snippet = {'title': '', 'tag': '', 'cmd': '', 'doc': ''}
        dialog = EditSnippetDialog(self, snippet)
        dialog.on_accept(self._on_create_dialog_accept)
        self.open_dialog(dialog, title='New snippet')

    def _on_model_rows_loaded(self, model: SnippetsModel, rows):
        self._table_store.load(rows)

    def _on_model_row_created(self, model, row):
        self._table_store.insert(0, row)
        self.close_dialog()

    def _on_model_row_deleted(self, model, rowid):
        index, row = self._table_store.find(lambda r: r['id'] == rowid)
        if index is not None:
            self._table_store.delete(index)

    def _on_model_row_updated(self, model, rowid, snippet):
        index, row = self._table_store.find(lambda r: r['id'] == rowid)
        if index is not None:
            self._table_store.update(index, snippet)
        self.close_dialog()

    def keypress(self, size, key):
        key = super().keypress(size, key)
        if not key:
            return
        if key == '?':
            # TODO: help screen
            return
        if key == 'f2':
            self._open_sort_dialog()
            return
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
        if key in ('-', 'd', 'delete'):
            self._on_delete_snippet_requested()
            return
        if key in ('+', 'i', 'insert'):
            self._open_create_dialog()
            return
        if key == 'e':
            self._open_edit_dialog()
            return
        logger.debug(key)
        return key

    def _on_search_term_changed(self, entry, text):
        self._emit('search-changed', text)

    def _on_snippet_list_row_selected(self, table, row):
        snippet = self._model.get(row['id'])
        self._emit('snippet-selected', snippet)

    def _on_sort_column_selected(self, dialog, column, order):
        self._emit('sort-column-selected', column, order)

    def _on_page_size_changed(self, dialog, page_size):
        self._emit('page-size-changed', page_size)

    def _on_delete_snippet_requested(self):
        row = self.snippet_list.get_selected()
        if not row:
            return
        msg = 'Are you sure you want to delete this snippet ?'
        dialog = ConfirmDialog(self, msg)
        dialog.on_accept(lambda *x: self._emit('delete-snippet-requested', row['id']))
        self.open_dialog(dialog, 'Caution !')

    def _on_edit_dialog_accept(self, snippet):
        self._emit('edit-snippet-requested', snippet)

    def _on_create_dialog_accept(self, snippet):
        self._emit('create-snippet-requested', snippet)
