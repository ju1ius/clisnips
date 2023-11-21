from collections.abc import Iterable, Mapping, Sequence
import sqlite3
from typing import Any, Literal, Self, TypeAlias

from clisnips.database.snippets_db import QueryParameters

from . import ScrollDirection, SortOrder
from .offset_pager import OffsetPager
from .pager import Page, Row

CursorColumn: TypeAlias = tuple[str, SortOrder]
# column: (name: str, order: SortOrder[, unique: bool])
SortColumnDefinition: TypeAlias = CursorColumn | tuple[str, SortOrder, bool]


class ScrollingPager(OffsetPager[Row]):
    def __init__(
        self,
        connection: sqlite3.Connection,
        page_size: int = 100,
        sort_columns: Iterable[SortColumnDefinition] | None = None,
    ):
        super().__init__(connection, page_size)
        # Keeps track of the resultset bounds after each query
        self._cursor = Cursor.with_columns(sort_columns) if sort_columns else Cursor()

    def get_sort_columns(self):
        return self._cursor.sort_columns

    def set_sort_columns(self, columns: Iterable[SortColumnDefinition]):
        self._cursor = Cursor.with_columns(columns)

    def execute(self, params: QueryParameters = (), count_params: QueryParameters = ()) -> Self:
        super().execute(params, count_params)
        return self

    def get_page(self, page: int) -> Page[Row]:
        self._check_executed()
        if page <= 1:
            self._current_page = 1
            return self.first()
        elif page >= self._page_count:
            self._current_page = self._page_count
            return self.last()
        self._current_page = page
        offset = (page - 1) * self._page_size
        query = self._get_page_fmt.format(offset=offset)
        rs = self._con.execute(query, self._query_params).fetchall()
        self._cursor.update(rs)
        return rs

    def first(self) -> Page[Row]:
        self._check_executed()
        self._current_page = 1
        query, params = self._first_query, self._query_params
        rs = self._con.execute(query, params).fetchall()
        self._cursor.update(rs)
        return rs

    def last(self) -> Page[Row]:
        self._check_executed()
        self._current_page = self._page_count
        query, params = self._last_query, self._query_params
        rs = self._con.execute(query, params).fetchall()
        # reverse result set
        rs.reverse()
        self._cursor.update(rs)
        return rs

    def next(self) -> Page[Row]:
        self._check_executed()
        if self._current_page >= self._page_count:
            return self.last()
        self._current_page += 1
        query = self._next_fmt.format(cursor=self._cursor)
        rs = self._con.execute(query, self._query_params).fetchall()
        self._cursor.update(rs)
        return rs

    def previous(self) -> Page[Row]:
        self._check_executed()
        if self._current_page <= 2:
            return self.first()
        self._current_page -= 1
        query = self._prev_fmt.format(cursor=self._cursor)
        rs = self._con.execute(query, self._query_params).fetchall()
        # reverse result set
        rs.reverse()
        self._cursor.update(rs)
        return rs

    def count(self):
        super().count()
        self._compile_queries()

    def _compile_queries(self):
        query = self._query
        fwd_orderby = self._cursor.as_order_by_clause(ScrollDirection.FWD)
        bwd_orderby = self._cursor.as_order_by_clause(ScrollDirection.BWD)
        fwd_where = self._cursor.as_where_clause(ScrollDirection.FWD, 'cursor')
        bwd_where = self._cursor.as_where_clause(ScrollDirection.BWD, 'cursor')
        # we have to compute the number of remaining rows on the last page
        remaining_rows = self._total_size % self._page_size
        if remaining_rows == 0:
            last_page_size = self._page_size
        else:
            last_page_size = remaining_rows
        # query for self.first()
        self._first_query = f'SELECT * FROM ({query}) ORDER BY {fwd_orderby} LIMIT {self._page_size}'
        # query for self.last()
        self._last_query = f'SELECT * FROM ({query}) ORDER BY {bwd_orderby} LIMIT {last_page_size}'
        # query for self.next()
        self._next_fmt = f'SELECT * FROM ({query}) WHERE ({fwd_where}) ORDER BY {fwd_orderby} LIMIT {self._page_size}'
        # query for self.previous()
        self._prev_fmt = f'SELECT * FROM ({query}) WHERE ({bwd_where}) ORDER BY {bwd_orderby} LIMIT {self._page_size}'
        # query for self.get_page()
        self._get_page_fmt = f'SELECT * FROM ({query}) ORDER BY {fwd_orderby} LIMIT {self._page_size} OFFSET {{offset}}'

    def _is_unique_column(self, column_name: str, table_name: str):
        # PRAGMA INDEX_LIST(table_name)
        # => [{'seq': unique id of the index,
        #      'name': name of the index,
        #      'unique': nonzero if unique index
        #    }, ...]
        indexes = self._con.execute(f'PRAGMA index_list({table_name})').fetchall()
        for idx in indexes:
            if idx['unique'] == 0:
                continue
            idx_info = self._con.execute(f'PRAGMA index_info({idx["name"]})').fetchone()
            if idx_info['name'] == column_name:
                return True
        return False


_WHERE_OP: dict[tuple[ScrollDirection, SortOrder], Literal['<', '>']] = {
    (ScrollDirection.FWD, SortOrder.ASC): '>',
    (ScrollDirection.FWD, SortOrder.DESC): '<',
    (ScrollDirection.BWD, SortOrder.ASC): '<',
    (ScrollDirection.BWD, SortOrder.DESC): '>',
}


def _get_operator(direction: ScrollDirection, order: SortOrder, unique: bool = False) -> Literal['<', '>', '<=', '>=']:
    operator = _WHERE_OP[(direction, order)]
    if not unique:
        operator += '='
    return operator


class Cursor:
    """
    Tracks a result set's bounds after each paginated query.

    The `first` and `last` members hold a mapping from column name to column value.
    The `first` member represents the first row of a page.
    The `last` member represents the last row of a page.
    """

    def __init__(
        self,
        unique_column: CursorColumn = ('rowid', SortOrder.ASC),
        sort_columns: Iterable[CursorColumn] | None = None,
    ) -> None:
        self._sort_columns: list[CursorColumn] = list(sort_columns or ())
        self._unique_column: CursorColumn = unique_column
        self._first: dict[str, Any] = {}
        self._last: dict[str, Any] = {}
        self.update(())

    @property
    def first(self):
        return self._first

    @property
    def last(self):
        return self._last

    @property
    def sort_columns(self) -> list[CursorColumn]:
        return self._sort_columns[:]

    @property
    def unique_column(self) -> CursorColumn:
        return self._unique_column

    @classmethod
    def with_columns(cls, columns: Iterable[SortColumnDefinition]) -> Self:
        unique_column = None
        sort_columns: list[CursorColumn] = []
        for name, order, *rest in columns:
            unique = bool(rest and rest[0])
            if unique:
                if unique_column:
                    raise RuntimeError('You can add only one unique sort column.')
                unique_column = (name, order)
                continue
            sort_columns.append((name, order))
        if not unique_column:
            raise RuntimeError('You must add an unique sort column. Consider adding ("rowid", SortOrder.ASC, True)')

        return cls(unique_column, sort_columns)

    def columns(self) -> Iterable[CursorColumn]:
        yield from self._sort_columns
        yield self._unique_column

    def column_names(self) -> Iterable[str]:
        return (n for n, _ in self.columns())

    def update(self, result_set: Sequence[Mapping[str, Any]]):
        if not result_set:
            self._first = {n: None for n in self.column_names()}
            self._last = {n: None for n in self.column_names()}
            return
        first_row = result_set[0]
        self._first = {n: first_row[n] for n in self.column_names()}
        last_row = result_set[-1]
        self._last = {n: last_row[n] for n in self.column_names()}

    def as_order_by_clause(self, direction: ScrollDirection) -> str:
        match direction:
            case ScrollDirection.FWD:
                return ', '.join(f'{name} {order}' for name, order in self.columns())
            case ScrollDirection.BWD:
                return ', '.join(f'{name} {order.reversed()}' for name, order in self.columns())

    def as_where_clause(self, direction: ScrollDirection, cursor_name: str = 'cursor') -> str:
        # value format, i.e. `{cursor.first[%s]!r}`
        value_fmt = '{%s.%s[%%s]!r}' % (  # noqa: UP031 (No, this is more readable!)
            cursor_name,
            'last' if direction is ScrollDirection.FWD else 'first',
        )
        # comparison format, i.e. `rowid >= {cursor.first['rowid']!r}`
        cmp_fmt = '{column} {op} {value}'

        # add unique column
        name, order = self._unique_column
        operator = _get_operator(direction, order, unique=True)
        key = value_fmt % name
        unique_expr = cmp_fmt.format(column=name, op=operator, value=key)
        if not self._sort_columns:
            return unique_expr

        # add non-unique columns
        left: list[str] = []
        right: list[str] = []
        for name, order in self._sort_columns:
            op1 = _get_operator(direction, order, unique=False)
            op2 = _get_operator(direction, order, unique=True)
            key = value_fmt % name
            # last_index = self._cursor[cursor][name]
            left.append(cmp_fmt.format(column=name, op=op1, value=key))
            right.append(cmp_fmt.format(column=name, op=op2, value=key))
        right.append(unique_expr)

        return '({left}) AND ({right})'.format(
            left=' AND '.join(left),
            right=' OR '.join(right),
        )
