import urwid

from clisnips.stores.snippets import QueryState, SnippetsStore
from clisnips.tui.widgets.edit import EmacsEdit
from clisnips.tui.widgets.utils import suspend_emitter


class SearchInput(EmacsEdit):
    def __init__(self, store: SnippetsStore):
        super().__init__(multiline=False)
        self._watchers = {
            'value': store.watch(lambda s: s['search_query'], self._on_query_changed, immediate=True),
            'state': store.watch(lambda s: s['query_state'], self._on_query_state_changed, immediate=True),
        }
        urwid.connect_signal(self, 'postchange', self._on_input_changed, weak_args=(store,))

    def _on_query_changed(self, value: str):
        with suspend_emitter(self):
            self.set_edit_text(value)

    def _on_query_state_changed(self, state: QueryState):
        match state:
            case QueryState.VALID:
                self.set_caption(('search-entry:caption', '?> '))
            case QueryState.INVALID:
                self.set_caption(('error', '!> '))

    def _on_input_changed(self, store: SnippetsStore, *_):
        store.change_search_query(self.get_edit_text())

    def get_search_text(self):
        return self.get_edit_text()
