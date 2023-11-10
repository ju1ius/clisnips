import atexit

from clisnips.dic import DependencyInjectionContainer
from .screens.snippets_list import SnippetsListScreen
from .tui import TUI


class Application:

    def __init__(self, dic: DependencyInjectionContainer):
        self.container = dic
        self.screen = None
        self.ui = TUI()
        self.ui.register_screen('snippets-list', self._build_snippets_list)
        atexit.register(self._on_exit)

    def run(self) -> int:
        self.activate_screen('snippets-list')
        self.ui.main()
        return 0

    def activate_screen(self, name: str, **kwargs):
        self.screen = self.ui.build_screen(name, display=True, **kwargs)
        self.ui.refresh()

    def _build_snippets_list(self, *args, **kwargs):
        screen = SnippetsListScreen(self.container.config, self.container.list_model, self.container.snippets_store)
        self.ui.connect(screen, SnippetsListScreen.Signals.SNIPPET_APPLIED, self._on_snippet_applied)
        return screen

    def _on_snippet_applied(self, command):
        self.ui.exit_with_message(command)

    def _on_exit(self):
        self.container.config.save()
        self.container.database.close()
