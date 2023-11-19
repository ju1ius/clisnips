import sqlite3
from pathlib import Path

import pytest

from clisnips.database.offset_pager import OffsetPager

FIXTURES = [
    ('test foo', 5),
    ('test bar', 6),
    ('test baz', 3),
    ('test qux', 4),
    ('test foobar', 8)
]


@pytest.fixture(scope='module')
def connection():
    con = sqlite3.connect(':memory:')
    con.row_factory = sqlite3.Row
    with open(Path(__file__).parent / 'pager_test.schema.sql') as fp:
        con.executescript(fp.read())
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
    yield con
    con.close()


def rowids(rows) -> list[int]:
    return [r['rowid'] for r in rows]


def test_simple_query(connection):
    pager = OffsetPager(connection, 5)
    pager.set_query('select rowid, * from paging_test')
    pager.execute()
    assert len(pager) == 4, 'Wrong number of pages.'
    expected = {
        1: [1, 2, 3, 4, 5],
        2: [6, 7, 8, 9, 10],
        3: [11, 12, 13, 14, 15],
        4: [16, 17, 18, 19, 20],
    }
    #
    first = pager.first()
    assert rowids(first) == expected[1], 'Failed fetching first page.'
    #
    last = pager.last()
    assert rowids(last) == expected[4], 'Failed fetching last page.'
    #
    page_2 = pager.get_page(2)
    assert rowids(page_2) == expected[2], 'Failed fetching page 2.'
    #
    page_3 = pager.next()
    assert rowids(page_3) == expected[3], 'Failed fetching next page (3).'
    #
    rs = pager.previous()
    assert rowids(rs) == expected[2], 'Failed fetching previous page (2).'
    #
    last = pager.last()
    assert pager.next() == last, 'Calling next on last page returns last page'
    first = pager.first()
    assert pager.previous() == first, 'Calling previous on first page returns first page'


def test_complex_query(connection):
    pager = OffsetPager(connection, 5)
    params = {'term': 'foo*'}
    expected = {
        1: [1, 5, 6, 10, 11],
        2: [15, 16, 20],
    }
    pager.set_query('''
        SELECT i.docid, t.rowid, t.* FROM paging_test t
        JOIN paging_test_idx i ON i.docid = t.rowid
        WHERE paging_test_idx MATCH :term
    ''', params)
    pager.set_count_query('''
        SELECT docid FROM paging_test_idx
        WHERE paging_test_idx MATCH :term
    ''', params)
    pager.execute()
    assert len(pager) == 2, 'Wrong number of pages.'
    #
    first = pager.first()
    assert rowids(first) == expected[1], 'Failed fetching first page.'
    #
    last = pager.next()
    assert rowids(last) == expected[2], 'Failed fetching next page (2).'
    #
    first = pager.previous()
    assert rowids(first) == expected[1], 'Failed fetching previous page (1).'
    #
    last = pager.last()
    assert rowids(last) == expected[2], 'Failed fetching last page.'
    #
    page_2 = pager.get_page(2)
    assert rowids(page_2) == expected[2], 'Failed fetching page 2.'
    #
    last = pager.last()
    assert pager.next() == last, 'Calling next on last page returns last page'
    first = pager.first()
    assert pager.previous() == first, 'Calling previous on first page returns first page'
