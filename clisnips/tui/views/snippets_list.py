import enum
import logging

import urwid
from urwid.canvas import CompositeCanvas

from clisnips.database import NewSnippet, Snippet
from clisnips.exceptions import ParseError
from clisnips.stores.snippets import ListLayout, SnippetsStore
from clisnips.syntax import parse_command, parse_documentation
from clisnips.tui.components.app_bar import AppBar
from clisnips.tui.components.delete_snippet_dialog import DeleteSnippetDialog
from clisnips.tui.components.edit_snippet_dialog import EditSnippetDialog
from clisnips.tui.components.help_dialog import HelpDialog
from clisnips.tui.components.insert_snippet_dialog import InsertSnippetDialog
from clisnips.tui.components.list_options_dialog import ListOptionsDialog
from clisnips.tui.components.pager_infos import PagerInfos
from clisnips.tui.components.search_input import SearchInput
from clisnips.tui.components.show_snippet_dialog import ShowSnippetDialog
from clisnips.tui.components.snippets_list import SnippetsList
from clisnips.tui.components.snippets_table import SnippetsTable
from clisnips.tui.components.syntax_error_dialog import SyntaxErrorDialog
from clisnips.tui.view import View

logger = logging.getLogger(__name__)


class SnippetListView(View):
    class Signals(enum.StrEnum):
        APPLY_SNIPPET_REQUESTED = enum.auto()

    signals = list(Signals)

    def __init__(self, store: SnippetsStore):
        self._store = store

        search_entry = SearchInput(store)
        pager_infos = PagerInfos(store)
        header = urwid.Columns((('weight', 1, search_entry), ('pack', pager_infos)), dividechars=1)
        self._list = SnippetsList(store)
        body = urwid.Frame(
            self._list,
            header=header,
            footer=AppBar(store),
            focus_part='header',
        )
        super().__init__(body)

        def handle_layout_changed(layout: ListLayout):
            logger.debug('layout: %r', layout)
            selected = self._list.get_selected_index()
            match layout:
                case ListLayout.LIST:
                    self._list = SnippetsList(store)
                case ListLayout.TABLE:
                    self._list = SnippetsTable(store)
            if selected is not None:
                self._list.set_selected_index(selected)
            body.body = self._list
            self._invalidate()

        def handle_viewport_changed(viewport):
            logger.debug('viewport: %r', viewport)

        self._watchers = {
            'viewport': self._store.watch(
                lambda s: s['viewport'],
                handle_viewport_changed,
                immediate=True,
                sync=True,
            ),
            'layout': self._store.watch(lambda s: s['list_layout'], handle_layout_changed, immediate=True),
        }

    def _get_selected_id(self) -> int | None:
        index = self._list.get_selected_index()
        if index is not None:
            return self._store.state['snippet_ids'][index]

    def _select_snippet(self):
        id = self._get_selected_id()
        if id is None:
            return
        snippet = self._store.fetch_snippet(id)
        logger.debug('selected %r', dict(snippet))

        def accept(rowid: int, cmd: str):
            self._store.use_snippet(rowid)
            self._emit(self.Signals.APPLY_SNIPPET_REQUESTED, cmd)

        def show_error_dialog():
            dialog = SyntaxErrorDialog(self)
            dialog.on_accept(lambda *_: self._open_edit_dialog(id))
            self.open_dialog(dialog, title='Syntax error')

        try:
            cmd = parse_command(snippet['cmd'])
        except ParseError as err:
            logger.warn(err)
            show_error_dialog()
            return
        if not cmd.has_fields():
            accept(snippet['id'], snippet['cmd'])
            return
        try:
            doc = parse_documentation(snippet['doc'])
        except ParseError as err:
            logger.warn(err)
            show_error_dialog()
            return

        dialog = InsertSnippetDialog(self, snippet['title'], cmd, doc)
        dialog.on_accept(lambda v: accept(snippet['id'], v))
        self.open_dialog(dialog, title='Insert snippet')

    def _open_prefs_dialog(self):
        dialog = ListOptionsDialog(self, self._store)
        self.open_dialog(dialog, title='List Options', width=35, height=15)

    def _open_show_dialog(self):
        id = self._get_selected_id()
        if id is None:
            return
        snippet = self._store.fetch_snippet(id)
        dialog = ShowSnippetDialog(self, snippet)
        self.open_dialog(dialog, title='Show snippet')

    def _open_create_dialog(self):
        dialog = EditSnippetDialog(self, NewSnippet({'title': '', 'tag': '', 'cmd': '', 'doc': ''}))
        dialog.on_accept(lambda s: self._store.create_snippet(s))
        self.open_dialog(dialog, title='New snippet')

    def _open_edit_dialog(self, id: int | None = None):
        id = id if id is not None else self._get_selected_id()
        if id is None:
            return
        snippet = self._store.fetch_snippet(id)
        dialog = EditSnippetDialog(self, Snippet(snippet))
        dialog.on_accept(lambda s: self._store.update_snippet(s))
        self.open_dialog(dialog, title='Edit snippet')

    def _open_delete_dialog(self):
        id = self._get_selected_id()
        if id is None:
            return
        dialog = DeleteSnippetDialog(self)
        dialog.on_accept(lambda *_: self._store.delete_snippet(id))
        self.open_dialog(dialog, 'Caution !')

    def _open_help_dialog(self):
        dialog = HelpDialog(self)
        self.open_dialog(dialog, 'Help')

    def render(self, size, focus: bool = False) -> CompositeCanvas:
        self._store.change_viewport(*size)
        return super().render(size, focus)

    def keypress(self, size, key):
        # logger.debug('size=%r, key=%r', size, key)
        key = super().keypress(size, key)
        focus = self._view.focus_position
        match key:
            case 'f1':
                self._open_help_dialog()
            case 'f2':
                self._open_prefs_dialog()
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
