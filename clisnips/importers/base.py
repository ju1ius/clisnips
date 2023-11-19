from abc import abstractmethod, ABC
from pathlib import Path
from collections.abc import Callable
import time

from pydantic import BaseModel, Field

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


class ImportableSnippet(BaseModel):
    id: int | None = None
    title: str
    cmd: str
    tag: str = ''
    doc: str = ''
    created_at: int = Field(default_factory=lambda: int(time.time()))
    last_used_at: int = 0
    usage_count: int = 0
    ranking: float = 0.0
