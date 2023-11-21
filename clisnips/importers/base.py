from abc import ABC, abstractmethod
from pathlib import Path
from typing_extensions import TypedDict

from pydantic import TypeAdapter

from clisnips.database import ImportableSnippet
from clisnips.database.snippets_db import SnippetsDatabase


class Importer(ABC):
    def __init__(self, db: SnippetsDatabase, dry_run=False):
        self._db = db
        self._dry_run = dry_run

    @abstractmethod
    def import_path(self, path: Path) -> None:
        return NotImplemented


class SnippetDocument(TypedDict):
    snippets: list[ImportableSnippet]


SnippetAdapter = TypeAdapter(ImportableSnippet)
SnippetListAdapter = TypeAdapter(list[ImportableSnippet])
SnippetDocumentAdapter = TypeAdapter(SnippetDocument)
