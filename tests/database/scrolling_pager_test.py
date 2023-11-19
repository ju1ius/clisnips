import sqlite3
from pathlib import Path

import pytest

from clisnips.database import SortOrder
from clisnips.database.scrolling_pager import ScrollingPager

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
    with open(Path(__file__).parent / 'pager_test.schema.sql') as fp:
        con.executescript(fp.read())
    rowid = 0
    for i in range(4):
        for value, ranking in FIXTURES:
            rowid += 1
            value = '%s #%s' % (value, rowid)
            con.execute(
                '''INSERT INTO paging_test(rowid, value, ranking) VALUES(?, ?, ?)''',
                (rowid, value, ranking)
            )
    yield con
    con.close()


def rowids(rows) -> list[int]:
    return [r['rowid'] for r in rows]


def test_simple_query(connection):
    pager = ScrollingPager(connection, 5)
    pager.set_query('select rowid, * from paging_test')
    pager.set_sort_columns([('rowid', SortOrder.ASC, True)])
    expected = {
        1: [1, 2, 3, 4, 5],
        2: [6, 7, 8, 9, 10],
        3: [11, 12, 13, 14, 15],
        4: [16, 17, 18, 19, 20],
    }
    first_index, last_index = min(expected.keys()), max(expected.keys())
    #
    pager.execute()
    assert len(pager) == len(expected), 'Wrong number of pages.'
    #
    first = pager.first()
    assert pager.current_page == first_index
    assert rowids(first) == expected[first_index], 'Failed fetching first page.'
    #
    last = pager.last()
    assert pager.current_page == last_index
    assert rowids(last) == expected[last_index], 'Failed fetching last page.'
    # fetch all pages in forward motion
    for i, ids in expected.items():
        rs = pager.first() if i == first_index else pager.next()
        assert pager.current_page == i
        assert rowids(rs) == ids, f'Failed fetching page {i}.'
    # fetch all pages in backward motion
    for i, ids in reversed(expected.items()):
        rs = pager.last() if i == last_index else pager.previous()
        assert pager.current_page == i
        assert rowids(rs) == ids, f'Failed fetching page {i}.'
    # fetch page by absolute offset
    page_2 = pager.get_page(2)
    assert pager.current_page == 2
    assert rowids(page_2) == expected[2], 'Failed fetching page 2.'
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
    expected = {
        1: [5, 10, 15, 20, 1],
        2: [6, 11, 16, 4, 9],
        3: [14, 19],
    }
    first_index, last_index = min(expected.keys()), max(expected.keys())
    #
    pager.execute()
    assert pager.total_rows == 12, 'Wrong number of rows.'
    assert len(pager) == len(expected), 'Wrong number of pages.'
    #
    first = pager.first()
    assert pager.current_page == first_index
    assert rowids(first) == expected[first_index], 'Failed fetching first page.'
    #
    last = pager.last()
    assert pager.current_page == last_index
    assert rowids(last) == expected[last_index], 'Failed fetching last page.'
    # fetch all pages in forward motion
    for i, ids in expected.items():
        rs = pager.first() if i == first_index else pager.next()
        assert pager.current_page == i
        assert rowids(rs) == ids, f'Failed fetching page {i}.'
    # fetch all pages in backward motion
    for i, ids in reversed(expected.items()):
        rs = pager.last() if i == last_index else pager.previous()
        assert pager.current_page == i
        assert rowids(rs) == ids, f'Failed fetching page {i}.'
    #
    page_2 = pager.get_page(2)
    assert pager.current_page == 2
    assert rowids(page_2) == expected[2], 'Failed fetching page 2.'
    #
    last = pager.last()
    assert pager.next() == last, 'Calling next on last page returns last page'
    first = pager.first()
    assert pager.previous() == first, 'Calling previous on first page returns first page'
