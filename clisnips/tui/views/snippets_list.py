import enum
import logging

import urwid

from clisnips.exceptions import ParsingError
from clisnips.stores import SnippetsStore
from clisnips.syntax import parse_command
from clisnips.tui.components.list_options_dialog import ListOptionsDialog
from clisnips.tui.components.pager_infos import PagerInfos
from clisnips.tui.components.search_entry import SearchEntry
from clisnips.tui.view import View
from clisnips.tui.widgets.dialogs.confirm import ConfirmDialog
from clisnips.tui.widgets.dialogs.edit_snippet import EditSnippetDialog
from clisnips.tui.widgets.dialogs.help import HelpDialog
from clisnips.tui.widgets.dialogs.insert_snippet import InsertSnippetDialog
from clisnips.tui.widgets.dialogs.show_snippet import ShowSnippetDialog
from clisnips.tui.widgets.table import Column, Table, TableStore


class SnippetListView(View):

    class Signals(str, enum.Enum):
        APPLY_SNIPPET_REQUESTED = 'apply-snippet-requested'

    signals = list(Signals)

    def __init__(self, store: SnippetsStore):
        self._store = store

        search_entry = SearchEntry(store, ' ')
        pager_infos = PagerInfos(store)
        header = urwid.Columns((('weight', 1, search_entry), ('pack', pager_infos)), dividechars=1)

        self._table_store = TableStore()
        self.snippet_list = Table(self._table_store)
        self.snippet_list.append_column(Column('cmd'))
        self.snippet_list.append_column(Column('title'))
        self.snippet_list.append_column(Column('tag'))
        urwid.connect_signal(self.snippet_list, 'row-selected', self._on_snippet_list_row_selected)

        footer = urwid.Columns(
            (
                ('pack', urwid.Text('F1 Help')),
                ('pack', urwid.Text('F2 Sort')),
                ('pack', urwid.Text('ESC Quit')),
            ),
            dividechars=1,
        )

        body = urwid.Frame(
            self.snippet_list,
            header=header,
            footer=footer,
            focus_part='header',
        )
        super().__init__(body)

        def on_snippets_changed(snippets: dict[str, dict]):
            self._table_store.load(list(snippets.values()))

        self._watchers = {
            'snippets': store.watch(lambda s: s['snippets_by_id'], on_snippets_changed, immediate=True),
        }

    def _open_sort_dialog(self):
        dialog = ListOptionsDialog(self, self._store)
        self.open_dialog(dialog, title='List Options', width=35, height=14)

    def _open_show_dialog(self):
        row = self.snippet_list.get_selected()
        if not row:
            return
        snippet = self._store.fetch_snippet(row['id'])
        dialog = ShowSnippetDialog(self, snippet)
        self.open_dialog(dialog, title='Show snippet')

    def _open_create_dialog(self):
        def on_accept(snippet):
            self._store.create_snippet(snippet)
            # TODO: this should be reactive
            self._table_store.insert(0, snippet)
            self.close_dialog()

        snippet = {'title': '', 'tag': '', 'cmd': '', 'doc': ''}
        dialog = EditSnippetDialog(self, snippet)
        dialog.on_accept(on_accept)
        self.open_dialog(dialog, title='New snippet')

    def _open_edit_dialog(self):
        def on_accept(snippet):
            self._store.update_snippet(snippet)
            index, _ = self._table_store.find(lambda r: r['id'] == snippet['id'])
            if index is not None:
                self._table_store.update(index, snippet)
            self.close_dialog()

        row = self.snippet_list.get_selected()
        if not row:
            return
        snippet = self._store.fetch_snippet(row['id'])
        dialog = EditSnippetDialog(self, snippet)
        dialog.on_accept(on_accept)
        self.open_dialog(dialog, title='Edit snippet')

    def _open_delete_dialog(self):
        row = self.snippet_list.get_selected()
        if not row:
            return

        def on_accept(*_):
            self._store.delete_snippet(row['id'])
            index, _ = self._table_store.find(lambda r: r['id'] == row['id'])
            if index is not None:
                self._table_store.delete(index)

        dialog = ConfirmDialog(self, 'Are you sure you want to delete this snippet ?')
        dialog.on_accept(on_accept)
        self.open_dialog(dialog, 'Caution !')

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
            self._store.request_next_page()
            return
        if key == 'p':
            self._store.request_previous_page()
            return
        if key == 'f':
            self._store.request_first_page()
            return
        if key == 'l':
            self._store.request_last_page()
            return
        if key == 's':
            self._open_show_dialog()
            return
        if key in ('-', 'd', 'delete'):
            self._open_delete_dialog()
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
        # snippet = self._store.state['snippets_by_id'][row['id']]
        snippet = self._store.fetch_snippet(row['id'])
        logging.getLogger(__name__).debug('selected %r', dict(snippet))
        try:
            cmd = parse_command(snippet['cmd'])
        except ParsingError as err:
            # TODO: display the error
            return
        if not cmd.field_names:
            self._emit(self.Signals.APPLY_SNIPPET_REQUESTED, snippet['cmd'])
            # urwid.emit_signal(self, self.Signals.APPLY_SNIPPET_REQUESTED, snippet['cmd'])
            return

        dialog = InsertSnippetDialog(self, snippet)
        dialog.on_accept(lambda v: self._emit(self.Signals.APPLY_SNIPPET_REQUESTED, v))
        self.open_dialog(dialog, title='Insert snippet')
