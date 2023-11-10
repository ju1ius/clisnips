import sqlite3

import pytest

from clisnips.database import SortOrder
from clisnips.database.scrolling_pager import ScrollingPager

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
    ('foo', 5),
    ('bar', 6),
    ('baz', 3),
    ('foobarbaz', 4),
    ('foobar', 8),
]


@pytest.fixture(scope='module')
def connection():
    con = sqlite3.connect(':memory:')
    con.row_factory = sqlite3.Row
    con.executescript(TEST_SCHEMA)
    rowid = 0
    for i in range(4):
        for value, ranking in FIXTURES:
            rowid += 1
            value = '%s #%s' % (value, rowid)
            con.execute(
                '''insert into paging_test(rowid, value, ranking) values(?, ?, ?)''',
                (rowid, value, ranking)
            )
    yield con
    con.close()


def test_simple_query(connection):
    pager = ScrollingPager(connection, 5)
    pager.set_query('select rowid, * from paging_test')
    pager.set_sort_columns([('rowid', SortOrder.ASC, True)])
    #
    pager.execute()
    assert len(pager) == 4, 'Wrong number of pages.'
    #
    first = pager.first()
    ids = [r['rowid'] for r in first]
    assert ids == [1, 2, 3, 4, 5], 'Failed fetching first page.'
    #
    last = pager.last()
    ids = [r['rowid'] for r in last]
    assert ids == [16, 17, 18, 19, 20], 'Failed fetching last page.'
    #
    page_2 = pager.get_page(2)
    ids = [r['rowid'] for r in page_2]
    assert ids == [6, 7, 8, 9, 10], 'Failed fetching page 2.'
    #
    page_3 = pager.next()
    ids = [r['rowid'] for r in page_3]
    assert ids == [11, 12, 13, 14, 15], 'Failed fetching next page (3).'
    #
    rs = pager.previous()
    assert rs == page_2, 'Failed fetching previous page (2).'
    #
    last = pager.last()
    assert pager.next() == last, 'Calling next on last page returns last page'
    #
    first = pager.first()
    assert pager.previous() == first, 'Calling previous on first page returns first page'


def test_complex_query(connection):
    pager = ScrollingPager(connection, 5)
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
    pager.set_sort_columns([('ranking', SortOrder.DESC), ('rowid', SortOrder.ASC, True)])
    #
    pager.execute()
    assert pager._total_size == 12, 'Wrong number of rows.'
    assert len(pager) == 3, 'Wrong number of pages.'
    #
    page_1_ids = [5, 10, 15, 20, 1]
    page_2_ids = [6, 11, 16, 4, 9]
    page_3_ids = [14, 19]
    #
    first = pager.first()
    ids = [r['rowid'] for r in first]
    assert ids == page_1_ids, 'Failed fetching first page.'
    #
    page_2 = pager.next()
    ids = [r['rowid'] for r in page_2]
    assert ids == page_2_ids, 'Failed fetching next page (2).'
    #
    page_3 = pager.next()
    ids = [r['rowid'] for r in page_3]
    assert ids == page_3_ids, 'Failed fetching next page (3).'
    #
    page_2 = pager.previous()
    ids = [r['rowid'] for r in page_2]
    assert ids == page_2_ids, 'Failed fetching previous page (2).'
    #
    page_1 = pager.previous()
    ids = [r['rowid'] for r in page_1]
    assert ids == page_1_ids, 'Failed fetching previous page (1).'
    #
    last = pager.last()
    ids = [r['rowid'] for r in last]
    assert ids == page_3_ids, 'Failed fetching last page.'
    #
    page_2 = pager.get_page(2)
    ids = [r['rowid'] for r in page_2]
    assert ids == page_2_ids, 'Failed fetching page 2.'
    #
    last = pager.last()
    assert pager.next() == last, 'Calling next on last page returns last page'
    first = pager.first()
    assert pager.previous() == first, 'Calling previous on first page returns first page'
