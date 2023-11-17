
from abc import abstractmethod, ABC
from collections.abc import Callable
from pathlib import Path

from clisnips.database.snippets_db import SnippetsDatabase


class Exporter(ABC):
    def __init__(self, db: SnippetsDatabase, log: Callable[..., None]):
        self._db = db
        self._log = log

    @abstractmethod
    def export(self, path: Path):
        return NotImplemented
