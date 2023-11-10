import urwid

from clisnips.stores import SnippetsStore
from clisnips.tui.widgets.edit import EmacsEdit
from clisnips.tui.widgets.utils import suspend_emitter


class SearchInput(EmacsEdit):

    def __init__(self, store: SnippetsStore, caption: str):
        super().__init__(('search-entry:caption', caption), multiline=False)

        self._watchers = {
            'value': store.watch(lambda s: s['search_query'], self._on_state_changed, immediate=True)
        }
        urwid.connect_signal(self, 'postchange', self._on_input_changed, weak_args=(store,))

    def _on_state_changed(self, value: str):
        with suspend_emitter(self):
            self.set_edit_text(value)

    def _on_input_changed(self, store: SnippetsStore, *_):
        store.change_search_query(self.get_edit_text())

    def get_search_text(self):
        # urwid.Edit.get_text() returns the caption by default...
        return self.get_edit_text()
