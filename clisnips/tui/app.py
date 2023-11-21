import atexit
from collections.abc import Hashable

from clisnips.config.state import save_persistent_state
from clisnips.dic import DependencyInjectionContainer

from .tui import TUI
from .views.snippets_list import SnippetListView


class Application:
    def __init__(self, dic: DependencyInjectionContainer):
        self.container = dic
        self.current_view = None
        self.ui = TUI(dic.config.palette)
        self.ui.register_view('snippets-list', self._build_snippets_list)
        atexit.register(self._on_exit)

    def run(self) -> int:
        self.activate_view('snippets-list')
        self.ui.main()
        return 0

    def activate_view(self, name: Hashable, **kwargs):
        self.current_view = self.ui.build_view(name, display=True, **kwargs)
        self.ui.refresh()

    def _build_snippets_list(self, *args, **kwargs):
        view = SnippetListView(self.container.snippets_store)
        self.ui.connect(view, SnippetListView.Signals.APPLY_SNIPPET_REQUESTED, self._on_apply_snippet_requested)
        return view

    def _on_apply_snippet_requested(self, view: SnippetListView, command: str):
        self.ui.exit_with_message(command)

    def _on_exit(self):
        save_persistent_state(self.container.snippets_store.state)
        self.container.database.close()
