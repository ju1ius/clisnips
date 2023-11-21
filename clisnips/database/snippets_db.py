import math
import os
import sqlite3
import stat
from collections.abc import Iterable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any, Literal, Self, TypeAlias

from clisnips.ty import AnyPath

from . import Column, ImportableSnippet, NewSnippet, Snippet

__DIR__ = Path(__file__).absolute().parent


SECONDS_TO_DAYS = float(60 * 60 * 24)
# ranking decreases much faster for older items
# when gravity is increased
GRAVITY = 1.2

with open(__DIR__ / 'schema.sql') as fp:
    SCHEMA_QUERY = fp.read()


QueryParameter: TypeAlias = str | int | float
QueryParameters: TypeAlias = Sequence[QueryParameter] | Mapping[str, QueryParameter]


def compute_ranking(created: int, last_used: int, num_used: int, now: float) -> float:
    assert num_used > 0, 'Ranking must be computed after a snippet is used.'
    assert now > created, 'Ranking must not be computed for newly created snippets.'
    assert now > last_used, 'Ranking must not be computed after updating the usage timestamp.'

    age = (now - created) / SECONDS_TO_DAYS
    last_used_days = (now - last_used) / SECONDS_TO_DAYS
    return num_used / pow(last_used_days / age, GRAVITY)


# TODO: test this frecency algo for sorting
LOG_2 = math.log(2)
FRECENCY_HALF_LIFE = SECONDS_TO_DAYS
FRECENCY_DECAY = LOG_2 / FRECENCY_HALF_LIFE


def compute_frecency(now: float, previous: float) -> float:
    current_decay = now * FRECENCY_DECAY
    if previous == 0.0:
        return current_decay
    return math.log(math.exp(previous - current_decay) + 1) + current_decay


class SnippetNotFound(RuntimeError):
    def __init__(self, *args: Any):
        super().__init__('Snippet not found.', *args)


class SnippetsDatabase:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.cursor = connection.cursor()
        self.closed = False
        self.block_size = 1024
        self._num_rows = 0

    @classmethod
    def open(cls, db_file: AnyPath = ':memory:') -> Self:
        db_file = Path(db_file)
        if db_file.name != ':memory:' and not db_file.is_file():
            db_file.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
            os.mknod(db_file, 0o644 | stat.S_IFREG)
        cx = sqlite3.connect(db_file)
        cx.row_factory = sqlite3.Row
        cx.executescript(SCHEMA_QUERY)

        return cls(cx)

    def get_connection(self) -> sqlite3.Connection:
        return self.connection

    def get_cursor(self) -> sqlite3.Cursor:
        return self.cursor

    def save(self):
        if self.connection.total_changes > 0:
            self.connection.commit()

    def close(self):
        if not self.closed:
            self.save()
            self.connection.close()
            self.closed = True

    def __len__(self):
        if not self._num_rows:
            self.cursor.execute('SELECT COUNT(rowid) AS count FROM snippets')
            self._num_rows = self.cursor.fetchone()['count']
        return self._num_rows

    def rebuild_index(self):
        query = 'INSERT INTO snippets_index(snippets_index) VALUES("rebuild")'
        with self.connection:
            self.cursor.execute(query)

    def optimize_index(self):
        query = 'INSERT INTO snippets_index(snippets_index) VALUES("optimize")'
        with self.connection:
            self.cursor.execute(query)

    def __iter__(self) -> Iterator[Snippet]:
        return self.iter('*')

    def iter(self, *columns: Column | Literal['*']) -> Iterator[Snippet]:
        query = 'SELECT rowid AS id, %s from snippets' % ','.join(columns)
        with self.connection:
            self.cursor.execute(query)
            while rows := self.cursor.fetchmany(self.block_size):
                yield from rows

    def get(self, rowid: int) -> Snippet:
        if snippet := self.find(rowid):
            return snippet
        raise SnippetNotFound(rowid)

    def find(self, rowid: int) -> Snippet | None:
        query = 'SELECT rowid AS id, * FROM snippets WHERE rowid = :id'
        return self.cursor.execute(query, {'id': rowid}).fetchone()

    @staticmethod
    def get_listing_query() -> str:
        return 'SELECT rowid AS id, title, cmd, tag, created_at, last_used_at, usage_count, ranking FROM snippets'

    @staticmethod
    def get_listing_count_query() -> str:
        return 'SELECT rowid FROM snippets'

    @staticmethod
    def get_search_query() -> str:
        return """
            SELECT i.rowid as docid, s.rowid AS id,
            s.title, s.cmd, s.tag,
            s.created_at, s.last_used_at, s.usage_count, s.ranking
            FROM snippets s JOIN snippets_index i ON i.rowid = s.rowid
            WHERE snippets_index MATCH :term
        """

    @staticmethod
    def get_search_count_query() -> str:
        return 'SELECT rowid FROM snippets_index WHERE snippets_index MATCH :term'

    def search(self, term: str) -> list[Snippet]:
        query = 'SELECT rowid AS id FROM snippets_index WHERE snippets_index MATCH :term'
        try:
            return self.cursor.execute(query, {'term': term}).fetchall()
        except sqlite3.OperationalError:
            return []

    def insert(self, data: NewSnippet) -> int:
        query = 'INSERT INTO snippets(title, cmd, doc, tag) VALUES(:title, :cmd, :doc, :tag)'
        with self.connection:
            self.cursor.execute(query, data)
            if self.cursor.rowcount > 0:
                self._num_rows += self.cursor.rowcount
            return self.cursor.lastrowid  # type: ignore

    def insert_many(self, data: Iterable[ImportableSnippet]):
        query = """
            INSERT INTO snippets(
                title, cmd, doc, tag,
                created_at, last_used_at, usage_count, ranking
            )
            VALUES(
                :title, :cmd, :doc, :tag,
                :created_at, :last_used_at, :usage_count, :ranking
            )
        """
        with self.connection:
            self.cursor.executemany(query, data)
            if self.cursor.rowcount > 0:
                self._num_rows += self.cursor.rowcount

    def update(self, data: Snippet) -> int:
        query = 'UPDATE snippets SET title = :title, cmd = :cmd, doc = :doc, tag = :tag WHERE rowid = :id'
        with self.connection:
            self.cursor.execute(query, data)
            return self.cursor.rowcount

    def delete(self, rowid: int):
        query = 'DELETE FROM snippets WHERE rowid = :id'
        with self.connection:
            self.cursor.execute(query, {'id': rowid})
            if self.cursor.rowcount > 0:
                self._num_rows -= self.cursor.rowcount

    def use_snippet(self, rowid: int, now: float):
        snippet = self.get(rowid)
        ranking = compute_ranking(snippet['created_at'], snippet['last_used_at'], snippet['usage_count'] + 1, now)
        # ranking = compute_frecency(now, snippet['ranking'])
        query = (
            'UPDATE snippets '
            'SET last_used_at = :now, usage_count = usage_count + 1, ranking = :ranking '
            'WHERE rowid = :id'
        )
        with self.connection:
            self.cursor.execute(query, {'id': rowid, 'now': int(now), 'ranking': ranking})
