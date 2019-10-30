import logging
import os
from pathlib import Path

from .screens.snippets_list import SnippetsListScreen
from .tui import TUI
from ..database.snippets_db import SnippetsDatabase
from .logging import logger


class Application:

    def __init__(self):
        self._configure_logging()
        db_path = Path('~/.config/clisnips/snippets.sqlite').expanduser()
        self._db = SnippetsDatabase.open(db_path)
        self.ui = TUI()
        self.ui.register_screen('snippets-list', self._build_snippets_list)

    def run(self):
        # TODO: setup database connection, etc...
        self.ui.build_screen('snippets-list', display=True)
        self.ui.main()
        # TODO: cleanup database connection, etc...

    def _build_snippets_list(self, *args, **kwargs):
        screen = SnippetsListScreen(self._db)
        self.ui.connect(screen, 'snippet-applied', self._on_snippet_applied)
        return screen

    def _configure_logging(self):
        log_file = Path('~/.local/share/clisnips/tui.log').expanduser()
        log_file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        logger.addHandler(logging.FileHandler(log_file, 'w'))
        logger.setLevel(logging.DEBUG)

    def _on_snippet_applied(self, command):
        self.ui.exit_with_message(command)
