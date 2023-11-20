from abc import abstractmethod, ABC
from pathlib import Path

from clisnips.database.snippets_db import SnippetsDatabase


class Exporter(ABC):
    def __init__(self, db: SnippetsDatabase):
        self._db = db

    @abstractmethod
    def export(self, path: Path):
        return NotImplemented
