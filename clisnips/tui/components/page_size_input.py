import urwid
from urwid.numedit import IntegerEdit

from clisnips.stores.snippets import SnippetsStore
from clisnips.tui.widgets.utils import suspend_emitter


class PageSizeInput(IntegerEdit):
    def __init__(self, store: SnippetsStore, caption: str):
        super().__init__(caption)

        def on_state_changed(value: int):
            with suspend_emitter(self):
                self.set_edit_text(str(value))

        def on_value_changed(*_):
            value = self.value()
            if value is not None:
                store.change_page_size(max(1, min(100, int(value))))

        urwid.connect_signal(self, 'postchange', on_value_changed)
        self._watchers = {
            'value': store.watch(lambda s: s['page_size'], on_state_changed, immediate=True),
        }
