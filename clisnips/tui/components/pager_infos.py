import urwid

from clisnips.stores.snippets import SnippetsStore, State


class PagerInfos(urwid.Text):
    def __init__(self, store: SnippetsStore):
        super().__init__('Page 1/1 (0)', align='right')

        def compute_message(state: State):
            return f'Page {state["current_page"]}/{state["page_count"]} ({state["total_rows"]})'

        self._watcher = store.watch(
            compute_message,
            lambda text: self.set_text(text),
            immediate=True,
        )
