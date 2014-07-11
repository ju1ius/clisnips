import unittest
import sqlite3

from clisnips.database.offset_pager import OffsetPager


TEST_SCHEMA = '''
CREATE TABLE paging_test(
    value TEXT,
    ranking INTEGER
);

CREATE VIRTUAL TABLE paging_test_idx USING fts4(
    content="paging_test",
    value
);

CREATE TRIGGER IF NOT EXISTS test_bu BEFORE UPDATE
ON paging_test
BEGIN
    DELETE FROM paging_test_idx WHERE docid=OLD.rowid;
END;

CREATE TRIGGER IF NOT EXISTS test_bd BEFORE DELETE
ON paging_test
BEGIN
    DELETE FROM paging_test_idx WHERE docid=OLD.rowid;
END;

CREATE TRIGGER IF NOT EXISTS test_au AFTER UPDATE
ON paging_test
BEGIN
    INSERT INTO paging_test_idx(docid, value) VALUES(
        NEW.rowid, NEW.value
    );
END;

CREATE TRIGGER IF NOT EXISTS test_ai AFTER INSERT
ON paging_test
BEGIN
    INSERT INTO paging_test_idx(docid, value) VALUES(
        NEW.rowid, NEW.value
    );
END;
'''

FIXTURES = [
    ('test foo', 5),
    ('test bar', 6),
    ('test baz', 3),
    ('test qux', 4),
    ('test foobar', 8)
]


class OffsetPagerTest(unittest.TestCase):

    @classmethod
    def setUpClass(klass):
        con = sqlite3.connect(':memory:')
        con.row_factory = sqlite3.Row
        con.executescript(TEST_SCHEMA)
        rowid = 0
        for i in range(4):
            for value, ranking in FIXTURES:
                rowid += 1
                value = '%s #%s' % (value, rowid)
                con.execute(
                    '''insert into paging_test(rowid, value, ranking)
                    values(?, ?, ?)''',
                    (rowid, value, ranking)
                )
        klass.connection = con

    @classmethod
    def tearDownClass(klass):
        klass.connection.close()

    def testSimpleQuery(self):
        pager = OffsetPager(self.connection, 5)
        pager.set_query('select rowid, * from paging_test')
        pager.execute()
        self.assertEqual(len(pager), 4, 'Wrong number of pages.')
        #
        first = pager.first()
        ids = [r['rowid'] for r in first]
        self.assertEqual(ids, [1, 2, 3, 4, 5],
                         'Failed fetching first page.')
        #
        last = pager.last()
        ids = [r['rowid'] for r in last]
        self.assertEqual(ids, [16, 17, 18, 19, 20],
                         'Failed fetching last page.')
        #
        page_2 = pager.get_page(2)
        ids = [r['rowid'] for r in page_2]
        self.assertEqual(ids, [6, 7, 8, 9, 10],
                         'Failed fetching page 2.')
        #
        page_3 = pager.next()
        ids = [r['rowid'] for r in page_3]
        self.assertEqual(ids, [11, 12, 13, 14, 15],
                         'Failed fetching next page (3).')
        #
        rs = pager.previous()
        self.assertEqual(rs, page_2,
                         'Failed fetching previous page (2).')
        #
        last = pager.last()
        self.assertEqual(pager.next(), last,
                         'Calling next on last page returns last page')
        first = pager.first()
        self.assertEqual(pager.previous(), first,
                         'Calling previous on first page returns first page')

    def testComplexQuery(self):
        pager = OffsetPager(self.connection, 5)
        params = {'term': 'foo*'}
        pager.set_query('''
            SELECT i.docid, t.rowid, t.* from paging_test t
            JOIN paging_test_idx i ON i.docid = t.rowid
            WHERE paging_test_idx MATCH :term
        ''', params)
        pager.set_count_query('''
            SELECT docid FROM paging_test_idx
            WHERE paging_test_idx MATCH :term
        ''', params)
        pager.execute()
        self.assertEqual(len(pager), 2, 'Wrong number of pages.')
        #
        first = pager.first()
        ids = [r['rowid'] for r in first]
        self.assertEqual(ids, [1, 5, 6, 10, 11],
                         'Failed fetching first page.')
        #
        last = pager.next()
        ids = [r['rowid'] for r in last]
        self.assertEqual(ids, [15, 16, 20],
                         'Failed fetching next page (2).')
        #
        first = pager.previous()
        ids = [r['rowid'] for r in first]
        self.assertEqual(ids, [1, 5, 6, 10, 11],
                         'Failed fetching previous page (1).')
        #
        last = pager.last()
        ids = [r['rowid'] for r in last]
        self.assertEqual(ids, [15, 16, 20],
                         'Failed fetching last page.')
        #
        page_2 = pager.get_page(2)
        ids = [r['rowid'] for r in page_2]
        self.assertEqual(ids, [15, 16, 20],
                         'Failed fetching page 2.')
        #
        last = pager.last()
        self.assertEqual(pager.next(), last,
                         'Calling next on last page returns last page')
        first = pager.first()
        self.assertEqual(pager.previous(), first,
                         'Calling previous on first page returns first page')
