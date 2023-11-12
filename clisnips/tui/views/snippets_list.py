import enum
import logging
from typing import Optional

import urwid

from clisnips.exceptions import ParsingError
from clisnips.stores import SnippetsStore
from clisnips.syntax import parse_command
from clisnips.tui.components.edit_snippet_dialog import EditSnippetDialog
from clisnips.tui.components.help_dialog import HelpDialog
from clisnips.tui.components.insert_snippet_dialog import InsertSnippetDialog
from clisnips.tui.components.list_options_dialog import ListOptionsDialog
from clisnips.tui.components.pager_infos import PagerInfos
from clisnips.tui.components.search_input import SearchInput
from clisnips.tui.components.show_snippet_dialog import ShowSnippetDialog
from clisnips.tui.components.snippets_list import SnippetsList
# from clisnips.tui.components.snippets_table import SnippetsTable
from clisnips.tui.view import View
from clisnips.tui.widgets.dialogs.confirm import ConfirmDialog


class SnippetListView(View):

    class Signals(str, enum.Enum):
        APPLY_SNIPPET_REQUESTED = 'apply-snippet-requested'

    signals = list(Signals)

    def __init__(self, store: SnippetsStore):
        self._store = store

        search_entry = SearchInput(store, ' ')
        pager_infos = PagerInfos(store)
        header = urwid.Columns((('weight', 1, search_entry), ('pack', pager_infos)), dividechars=1)

        self._list = SnippetsList(store)
        # self._list = SnippetsTable(store)

        footer = urwid.Columns(
            (
                ('pack', urwid.Text('F1 Help')),
                ('pack', urwid.Text('F2 Sort')),
                ('pack', urwid.Text('ESC Quit')),
            ),
            dividechars=1,
        )

        body = urwid.Frame(
            self._list,
            header=header,
            footer=footer,
            focus_part='header',
        )
        super().__init__(body)
        
    def _get_selected_id(self) -> Optional[int]:
        index = self._list.get_selected_index()
        if index is not None:
            return self._store.state['snippet_ids'][index]

    def _select_snippet(self):
        id = self._get_selected_id()
        if id is None:
            return

        def accept(rowid: int, cmd: str):
            self._store.use_snippet(rowid)
            self._emit(self.Signals.APPLY_SNIPPET_REQUESTED, cmd)
            
        snippet = self._store.fetch_snippet(id)
        logging.getLogger(__name__).debug('selected %r', dict(snippet))
        try:
            cmd = parse_command(snippet['cmd'])
        except ParsingError as err:
            # TODO: display the error
            return
        if not cmd.field_names:
            accept(snippet['id'], snippet['cmd'])
            # urwid.emit_signal(self, self.Signals.APPLY_SNIPPET_REQUESTED, snippet['cmd'])
            return

        dialog = InsertSnippetDialog(self, snippet)
        dialog.on_accept(lambda v: accept(snippet['id'], v))
        self.open_dialog(dialog, title='Insert snippet')

    def _open_sort_dialog(self):
        dialog = ListOptionsDialog(self, self._store)
        self.open_dialog(dialog, title='List Options', width=35, height=14)

    def _open_show_dialog(self):
        id = self._get_selected_id()
        if id is None:
            return
        snippet = self._store.fetch_snippet(id)
        dialog = ShowSnippetDialog(self, snippet)
        self.open_dialog(dialog, title='Show snippet')

    def _open_create_dialog(self):
        snippet = {'title': '', 'tag': '', 'cmd': '', 'doc': ''}
        dialog = EditSnippetDialog(self, snippet)
        dialog.on_accept(lambda s: self._store.create_snippet(s))
        self.open_dialog(dialog, title='New snippet')

    def _open_edit_dialog(self):
        id = self._get_selected_id()
        if id is None:
            return
        snippet = self._store.fetch_snippet(id)
        dialog = EditSnippetDialog(self, snippet)
        dialog.on_accept(lambda s: self._store.update_snippet(s))
        self.open_dialog(dialog, title='Edit snippet')

    def _open_delete_dialog(self):
        id = self._get_selected_id()
        if id is None:
            return
        dialog = ConfirmDialog(self, 'Are you sure you want to delete this snippet ?')
        dialog.on_accept(lambda *_: self._store.delete_snippet(id))
        self.open_dialog(dialog, 'Caution !')

    def _open_help_dialog(self):
        dialog = HelpDialog(self)
        self.open_dialog(dialog, 'Help')

    def keypress(self, size, key):
        key = super().keypress(size, key)
        focus = self._view.focus_position
        match key:
            case 'f1':
                self._open_help_dialog()
            case 'f2':
                self._open_sort_dialog()
            case '/':
                self._view.focus_position = 'header'
            case 'tab' | 'shift tab' if focus == 'header':
                self._view.focus_position = 'body'
            case 'tab' | 'shift tab':
                self._view.focus_position = 'header'
            case 'down' if focus == 'header':
                self._view.focus_position = 'body'
            case 'up' if focus == 'body':
                self._view.focus_position = 'header'
            case 'n':
                self._store.request_next_page()
            case 'p':
                self._store.request_previous_page()
            case 'f':
                self._store.request_first_page()
            case 'l':
                self._store.request_last_page()
            case 'enter' if focus == 'body':
                self._select_snippet()
            case 's':
                self._open_show_dialog()
            case '+' | 'i' | 'insert':
                self._open_create_dialog()
            case '-' | 'd' | 'delete':
                self._open_delete_dialog()
            case 'e':
                self._open_edit_dialog()
            case _:
                return key
