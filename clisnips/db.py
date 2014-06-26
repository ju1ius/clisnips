import os
import stat
import time
import sqlite3


__DIR__ = os.path.abspath(os.path.dirname(__file__))

DB_FILE = os.path.join(__DIR__, 'snippets.sqlite')

SCHEMA_FILE = os.path.join(__DIR__, 'schema.sql')
with open(SCHEMA_FILE, 'r') as fp:
    SCHEMA_QUERY = fp.read()

SECONDS_TO_DAYS = float(60 * 60 * 24)
# ranking decreases much faster for older items
# when gravity is increased
GRAVITY = 1.2


def ranking_function(created, last_used, num_used):
    now = time.time()
    age = (now - created) / SECONDS_TO_DAYS
    last_used = (now - last_used) / SECONDS_TO_DAYS
    return num_used / pow(last_used / age, GRAVITY)


class SnippetsDatabase(object):

    COLUMN_ID = 'rowid'
    COLUMN_TITLE = 'title'
    COLUMN_CMD = 'cmd'
    COLUMN_TAGS = 'tag'
    COLUMN_DOC = 'doc'
    COLUMN_INDEX = 'docid'

    def __init__(self, db_file=None):
        self.db_file = db_file or DB_FILE
        self.connection = None
        self.cursor = None
        self.block_size = 1024

    def get_connection(self):
        return self.connection

    def get_cursor(self):
        return self.cursor

    def save(self):
        if self.connection.total_changes > 0:
            self.connection.commit()
        return self

    def close(self):
        self.save()
        self.connection.close()

    def open(self):
        if not os.path.isfile(self.db_file):
            os.mknod(self.db_file, 0o755 | stat.S_IFREG)
        if not isinstance(self.connection, sqlite3.Connection):
            self.connection = sqlite3.connect(self.db_file)
            self.connection.create_function('rank', 3, ranking_function)
            self.connection.executescript(SCHEMA_QUERY)
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
        return self

    def __len__(self):
        self.cursor.execute('SELECT COUNT(rowid) AS count FROM snippets')
        return self.cursor.fetchone()['count']

    def rebuild_index(self):
        query = ('INSERT INTO snippets_index(snippets_index) '
                 'VALUES("rebuild")')
        with self.connection:
            self.cursor.execute(query)

    def optimize_index(self):
        query = ('INSERT INTO snippets_index(snippets_index) '
                 'VALUES("optimize")')
        with self.connection:
            self.cursor.execute(query)

    def __iter__(self):
        return self.iter('*')

    def iter(self, *columns):
        query = 'SELECT rowid AS id, %s from snippets' % ','.join(columns)
        with self.connection:
            self.cursor.execute(query)
            while True:
                rows = self.cursor.fetchmany(self.block_size)
                if not rows:
                    return
                for row in rows:
                    yield row

    def get(self, rowid):
        query = ('SELECT rowid AS id, * FROM snippets WHERE rowid = :id')
        return self.cursor.execute(query, {'id': rowid}).fetchone()

    def search(self, term):
        query = ('SELECT docid AS id FROM snippets_index '
                 'WHERE snippets_index MATCH :term')
        try:
            rows = self.cursor.execute(query, {'term': term}).fetchall()
        except sqlite3.OperationalError as err:
            return []
        return rows

    def search2(self, term):
        query = ('SELECT rowid AS id, title, cmd, tag '
                 'FROM snippets WHERE rowid IN ('
                 '    SELECT docid FROM snippets_index '
                 '    WHERE snippets_index MATCH :term)')
        try:
            rows = self.cursor.execute(query, {'term': term}).fetchall()
        except sqlite3.OperationalError as err:
            return []
        return rows

    def insert(self, data):
        query = ('INSERT INTO snippets(title, cmd, doc, tag) '
                 'VALUES(:title, :cmd, :doc, :tag)')
        with self.connection:
            self.cursor.execute(query, data)
            return self.cursor.lastrowid

    def insertmany(self, data):
        query = ('INSERT INTO snippets(title, cmd, doc, tag) '
                 'VALUES(:title, :cmd, :doc, :tag)')
        with self.connection:
            self.cursor.executemany(query, data)
            return self.cursor.lastrowid

    def update(self, data):
        query = ('UPDATE snippets '
                 'SET title = :title, cmd = :cmd, doc = :doc, tag = :tag '
                 'WHERE rowid = :id')
        with self.connection:
            self.cursor.execute(query, data)

    def delete(self, rowid):
        query = 'DELETE FROM snippets WHERE rowid = :id'
        with self.connection:
            self.cursor.execute(query, {'id': rowid})

    def use_snippet(self, rowid):
        query = ('UPDATE snippets '
                 'SET last_used_at = strftime("%s", "now"), '
                 'usage_count = usage_count + 1 '
                 'WHERE rowid = ?')
        with self.connection:
            self.cursor.execute(query, (rowid,))
