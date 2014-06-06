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

INSERT OR REPLACE INTO snippets(rowid,title,cmd,doc,tag) VALUES(
    1,
    'List files in zip archive',
    'unzip -Z -1 {archive}',
    '{archive} (file) The path of the archive to extract',
    'zip,archive'
);
INSERT OR REPLACE INTO snippets(rowid,title,cmd,doc,tag) VALUES(
    2,
    'Untar',
    'tar -cxf {archive}',
    '{archive} (file) The path of the archive to extract',
    'tar,archive'
);
INSERT OR REPLACE INTO snippets(rowid,title,cmd,doc,tag) VALUES(
    3,
    'Compress PDF',
    'ghostscript -dSAFER -dNOPAUSE -dBATCH -sDEVICE=pdfwrite \\
        -dCompatibilityLevel=1.4 \\
        -dUseCIEColor -dColorConversionStrategy=/sRGB \\
        -dPDFSETTINGS=/{quality} \\
        -sOUTPUTFILE="{outfile}" -f "{infile}"',
    '{quality} (string) ["screen", "ebook", *"printer", "prepress"] Controls the quality of the output file
     {outfile} (string) The path to the compressed file
     {infile} (file) The path to the PDF to compress',
    'pdf,compression'
);
INSERT OR REPLACE INTO snippets(rowid,title,cmd,doc,tag) VALUES(
    4,
    'Convert to mp3 VBR',
    'sox {infile} -C {quality}.2 {outfile}',
    '
    {quality} (integer) [-9..0:1*-4] Quality of the compressed file from -9 (lowest) to 0 (highest)
    {infile} (file) The path to the file to convert
    {outfile} (file) The path to the converted file',
    'sox,mp3,vbr'
);
"""


class SnippetsDatabase(object):

    COLUMN_ID = 'rowid'
    COLUMN_TITLE = 'title'
    COLUMN_CMD = 'cmd'
    COLUMN_TAGS = 'tag'
    COLUMN_DOC = 'doc'

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
        return self.iter('rowid', '*')

    def iter(self, *columns):
        query = 'SELECT %s from snippets' % ','.join(columns)
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
        query = ('SELECT docid FROM snippets_index '
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
