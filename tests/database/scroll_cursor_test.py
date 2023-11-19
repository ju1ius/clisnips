
from clisnips.database import ScrollDirection, SortOrder
from clisnips.database.scrolling_pager import Cursor


def test_default_columns():
    cursor = Cursor()
    assert cursor.unique_column == ('rowid', SortOrder.ASC)
    assert cursor.sort_columns == []
    assert list(cursor.columns()) == [('rowid', SortOrder.ASC)]

    order_by = cursor.as_order_by_clause(ScrollDirection.FWD)
    assert order_by == 'rowid ASC'

    order_by = cursor.as_order_by_clause(ScrollDirection.BWD)
    assert order_by == 'rowid DESC'

    where = cursor.as_where_clause(ScrollDirection.FWD)
    assert where == 'rowid > {cursor.last[rowid]!r}'

    where = cursor.as_where_clause(ScrollDirection.BWD)
    assert where == 'rowid < {cursor.first[rowid]!r}'


def test_single_sort_column():
    cursor = Cursor.with_columns((
        ('foo', SortOrder.DESC),
        ('id', SortOrder.ASC, True),
    ))
    assert cursor.unique_column == ('id', SortOrder.ASC)
    assert cursor.sort_columns == [('foo', SortOrder.DESC)]
    assert list(cursor.columns()) == [
        ('foo', SortOrder.DESC),
        ('id', SortOrder.ASC),
    ]

    order_by = cursor.as_order_by_clause(ScrollDirection.FWD)
    assert order_by == 'foo DESC, id ASC'

    order_by = cursor.as_order_by_clause(ScrollDirection.BWD)
    assert order_by == 'foo ASC, id DESC'

    where = cursor.as_where_clause(ScrollDirection.FWD)
    assert where == '(foo <= {cursor.last[foo]!r}) AND (foo < {cursor.last[foo]!r} OR id > {cursor.last[id]!r})'

    where = cursor.as_where_clause(ScrollDirection.BWD)
    assert where == '(foo >= {cursor.first[foo]!r}) AND (foo > {cursor.first[foo]!r} OR id < {cursor.first[id]!r})'


def test_multiple_sort_columns():
    cursor = Cursor.with_columns((
        ('foo', SortOrder.DESC),
        ('id', SortOrder.ASC, True),
        ('bar', SortOrder.ASC),
    ))
    assert cursor.unique_column == ('id', SortOrder.ASC)
    assert cursor.sort_columns == [('foo', SortOrder.DESC), ('bar', SortOrder.ASC)]
    assert list(cursor.columns()) == [
        ('foo', SortOrder.DESC),
        ('bar', SortOrder.ASC),
        ('id', SortOrder.ASC),
    ]

    order_by = cursor.as_order_by_clause(ScrollDirection.FWD)
    assert order_by == 'foo DESC, bar ASC, id ASC'

    order_by = cursor.as_order_by_clause(ScrollDirection.BWD)
    assert order_by == 'foo ASC, bar DESC, id DESC'

    where = cursor.as_where_clause(ScrollDirection.FWD)
    assert where == (
        '(foo <= {cursor.last[foo]!r} AND bar >= {cursor.last[bar]!r})'
        ' AND (foo < {cursor.last[foo]!r} OR bar > {cursor.last[bar]!r} OR id > {cursor.last[id]!r})'
    )

    where = cursor.as_where_clause(ScrollDirection.BWD)
    assert where == (
        '(foo >= {cursor.first[foo]!r} AND bar <= {cursor.first[bar]!r})'
        ' AND (foo > {cursor.first[foo]!r} OR bar < {cursor.first[bar]!r} OR id < {cursor.first[id]!r})'
    )


def test_update():
    cursor = Cursor.with_columns((
        ('foo', SortOrder.DESC),
        ('bar', SortOrder.ASC),
        ('id', SortOrder.ASC, True),
    ))
    empty = {'id': None, 'foo': None, 'bar': None}
    assert cursor.first == cursor.last == empty

    rs = [
        {'id': 0, 'foo': 666, 'bar': 'first', 'baz': 'nope'},
        {'id': 1, 'foo': 333, 'bar': 'ignoreme', 'baz': 'nada'},
        {'id': 2, 'foo': 111, 'bar': 'last', 'baz': 'zilch'},
    ]
    cursor.update(rs)
    assert cursor.first == {'id': 0, 'foo': 666, 'bar': 'first'}
    assert cursor.last == {'id': 2, 'foo': 111, 'bar': 'last'}

    cursor.update([])
    assert cursor.first == cursor.last == empty

    cursor.update(rs[0:1])
    assert cursor.first == cursor.last == {'id': 0, 'foo': 666, 'bar': 'first'}
