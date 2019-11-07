import os
import sys
from typing import Optional

from .utils import UrwidMarkupHelper
from ..config import Config
from ..database.snippets_db import SnippetsDatabase


class Command:

    def __init__(self):
        self._markup_helper = UrwidMarkupHelper()

    def run(self, argv) -> Optional[int]:
        return NotImplemented

    def print(self, *args, stderr=False, end='\n'):
        stream = sys.stderr if stderr else sys.stdout
        tty = os.isatty(stream.fileno())
        output = ' '.join(self._markup_helper.convert_markup(m, tty) for m in args)
        print(output, end=end, file=stream)


class ConfigCommand(Command):

    _config: Config = None

    @property
    def config(self) -> Config:
        if not self._config:
            self._config = Config()
        return self._config


class DatabaseCommand(ConfigCommand):

    def open_database(self, argv) -> SnippetsDatabase:
        path = argv.database or self.config.database_path
        return SnippetsDatabase.open(path)
