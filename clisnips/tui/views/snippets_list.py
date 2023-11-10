import enum
import logging

import urwid

from clisnips.stores import SnippetsStore
from clisnips.tui.models.snippets import SnippetsModel
from clisnips.tui.view import View
from clisnips.tui.widgets.dialogs.confirm import ConfirmDialog
from clisnips.tui.widgets.dialogs.edit_snippet import EditSnippetDialog
from clisnips.tui.widgets.dialogs.help import HelpDialog
from clisnips.tui.widgets.dialogs.insert_snippet import InsertSnippetDialog
from clisnips.tui.components.list_options_dialog import ListOptionsDialog
from clisnips.tui.widgets.dialogs.show_snippet import ShowSnippetDialog
from clisnips.tui.components.pager_infos import PagerInfos
from clisnips.tui.components.search_entry import SearchEntry
from clisnips.tui.widgets.snippets_list_footer import SnippetListFooter
from clisnips.tui.widgets.table import Column, Table, TableStore


class SnippetListView(View):

    class Signals(str, enum.Enum):
        SEARCH_CHANGED = 'search-changed'
        SNIPPET_SELECTED = 'snippet-selected'
        SORT_COLUMN_SELECTED = 'sort-column-selected'
        SORT_ORDER_SELECTED = 'sort-order-selected'
        PAGE_SIZE_CHANGED = 'page-size-changed'
        PAGE_REQUESTED = 'page-requested'
        APPLY_SNIPPET_REQUESTED = 'apply-snippet-requested'
        CREATE_SNIPPET_REQUESTED = 'create-snippet-requested'
        DELETE_SNIPPET_REQUESTED = 'delete-snippet-requested'
        EDIT_SNIPPET_REQUESTED = 'edit-snippet-requested'
        HELP_REQUESTED = 'help-requested'

    signals = list(Signals)

    def __init__(self, model: SnippetsModel, store: SnippetsStore):
        self._store = store
        self._model = model
        self._model.connect(model.Signals.ROWS_LOADED, self._on_model_rows_loaded)
        self._model.connect(model.Signals.ROW_CREATED, self._on_model_row_created)
        self._model.connect(model.Signals.ROW_DELETED, self._on_model_row_deleted)
        self._model.connect(model.Signals.ROW_UPDATED, self._on_model_row_updated)

        self.search_entry = SearchEntry(store, ' ')
        pager_infos = PagerInfos(store)
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

        def on_snippets_changed(snippets: dict[str, dict]):
            self._table_store.load(list(snippets.values()))

        self._watchers = {
            'snippets': store.watch(lambda s: s['snippets_by_id'], on_snippets_changed, immediate=True),
        }

    def get_search_text(self):
        return self.search_entry.get_search_text()

    def open_insert_snippet_dialog(self, snippet):
        dialog = InsertSnippetDialog(self, snippet)
        dialog.on_accept(lambda v: self._emit(self.Signals.APPLY_SNIPPET_REQUESTED, v))
        self.open_dialog(dialog, title='Insert snippet')

    def _open_sort_dialog(self):
        dialog = ListOptionsDialog(self, self._store)
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

    def _open_help_dialog(self):
        dialog = HelpDialog(self)
        self.open_dialog(dialog, 'Help')

    def keypress(self, size, key):
        key = super().keypress(size, key)
        if not key:
            return
        if key == 'f1':
            self._open_help_dialog()
            return
        if key == 'f2':
            self._open_sort_dialog()
            return
        if key == '/':
            self.view.focus_position = 'header'
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
            self._emit(self.Signals.PAGE_REQUESTED, 'next')
            return
        if key == 'p':
            self._emit(self.Signals.PAGE_REQUESTED, 'previous')
            return
        if key == 'f':
            self._emit(self.Signals.PAGE_REQUESTED, 'first')
            return
        if key == 'l':
            self._emit(self.Signals.PAGE_REQUESTED, 'last')
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
        # logger.debug(key)
        return key

    def _on_snippet_list_row_selected(self, table, row):
        snippet = self._model.get(row['id'])
        self._emit(self.Signals.SNIPPET_SELECTED, snippet)

    def _on_delete_snippet_requested(self):
        row = self.snippet_list.get_selected()
        if not row:
            return
        msg = 'Are you sure you want to delete this snippet ?'
        dialog = ConfirmDialog(self, msg)
        dialog.on_accept(lambda *x: self._emit(self.Signals.DELETE_SNIPPET_REQUESTED, row['id']))
        self.open_dialog(dialog, 'Caution !')

    def _on_edit_dialog_accept(self, snippet):
        self._emit(self.Signals.EDIT_SNIPPET_REQUESTED, snippet)

    def _on_create_dialog_accept(self, snippet):
        self._emit(self.Signals.CREATE_SNIPPET_REQUESTED, snippet)
