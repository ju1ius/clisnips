
from abc import abstractmethod, ABC
from pathlib import Path
from collections.abc import Callable

from clisnips.database.snippets_db import SnippetsDatabase


class Importer(ABC):
    def __init__(
        self,
        db: SnippetsDatabase,
        log: Callable[..., None] = lambda *_: None,
        dry_run = False
    ):
        self._db = db
        self._log = log
        self._dry_run = dry_run

    @abstractmethod
    def import_path(self, path: Path) -> None:
        return NotImplemented
