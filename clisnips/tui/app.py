import atexit
import logging

from clisnips.config import xdg_data_home
from clisnips.dic import DependencyInjectionContainer
from .logging import logger
from .screens.snippets_list import SnippetsListScreen
from .tui import TUI


class Application:

    def __init__(self, dic: DependencyInjectionContainer):
        self.container = dic
        self.config = dic.config
        self._configure_logging()
        self.database = dic.database
        self.screen = None
        self.ui = TUI()
        self.ui.register_screen('snippets-list', self._build_snippets_list)
        atexit.register(self._on_exit)

    def run(self):
        self.activate_screen('snippets-list')
        self.ui.main()

    def activate_screen(self, name: str, **kwargs):
        self.screen = self.ui.build_screen(name, display=True, **kwargs)
        self.ui.refresh()

    def _build_snippets_list(self, *args, **kwargs):
        screen = SnippetsListScreen(self.config, self.container.list_model)
        self.ui.connect(screen, 'snippet-applied', self._on_snippet_applied)
        return screen

    def _configure_logging(self):
        log_file = xdg_data_home() / 'clisnips' / 'tui.log'
        log_file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        logger.addHandler(logging.FileHandler(log_file, 'w'))
        logger.setLevel(logging.DEBUG)

    def _on_snippet_applied(self, command):
        self.ui.exit_with_message(command)

    def _on_exit(self):
        self.config.save()
        self.database.close()
