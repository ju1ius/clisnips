import atexit
import logging

from .logging import logger
from .models.snippets import SnippetsModel
from .screens.snippets_list import SnippetsListScreen
from .tui import TUI
from ..config import Config, xdg_data_home
from ..database.snippets_db import SnippetsDatabase


class Application:

    def __init__(self):
        self.config = Config()
        self._configure_logging()
        self._db = None
        self.ui = TUI()
        self.ui.register_screen('snippets-list', self._build_snippets_list)
        atexit.register(self._on_exit)

    def run(self, argv):
        self._db = SnippetsDatabase.open(argv.database or self.config.database_path)
        self.ui.build_screen('snippets-list', display=True)
        self.ui.main()

    def _build_snippets_list(self, *args, **kwargs):
        model = SnippetsModel(self._db)
        screen = SnippetsListScreen(self.config, model)
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
        self._db.close()
