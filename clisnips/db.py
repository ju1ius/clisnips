import os
import stat
import sqlite3


__DIR__ = os.path.abspath(os.path.dirname(__file__))
DB_FILE = os.path.join(__DIR__, 'snippets.sqlite')

CREATE_TABLES_QUERY = """
CREATE TABLE IF NOT EXISTS snippets(
    title TEXT NOT NULL,
    cmd TEXT NOT NULL,
    doc TEXT,
    tag TEXT
);
CREATE VIRTUAL TABLE IF NOT EXISTS snippets_index USING fts4(
    content="snippets",
    title,
    tag
);

-- Triggers to keep snippets table and index in sync
CREATE TRIGGER IF NOT EXISTS snippets_bu BEFORE UPDATE ON snippets BEGIN
    DELETE FROM snippets_index WHERE docid=OLD.rowid;
END;
CREATE TRIGGER IF NOT EXISTS snippets_bd BEFORE DELETE ON snippets BEGIN
    DELETE FROM snippets_index WHERE docid=OLD.rowid;
END;

CREATE TRIGGER IF NOT EXISTS snippets_au AFTER UPDATE ON snippets BEGIN
    INSERT INTO snippets_index(docid, title, tag) VALUES(
        NEW.rowid, NEW.title, NEW.tag
    );
END;
CREATE TRIGGER IF NOT EXISTS snippets_ai AFTER INSERT ON snippets BEGIN
    INSERT INTO snippets_index(docid, title, tag) VALUES(
        NEW.rowid, NEW.title, NEW.tag
    );
END;
"""


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
            self.connection.executescript(CREATE_TABLES_QUERY)
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
        return self

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
            rows = self.cursor.fetchmany()
            while rows:
                for row in rows:
                    yield row
                rows = self.cursor.fetchmany()

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
        query = '''SELECT rowid AS id, title, cmd, tag
                    FROM snippets WHERE rowid IN (
                        SELECT docid FROM snippets_index
                        WHERE snippets_index MATCH :term
                  )'''
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
