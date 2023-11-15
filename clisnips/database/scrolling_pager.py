from typing import Iterable, Optional, Union

from . import ScrollDirection, SortOrder
from .offset_pager import OffsetPager

SortColumnDefinition = Union[tuple[str, SortOrder], tuple[str, SortOrder, bool]]

_WHERE_OP = {
    (ScrollDirection.FWD, SortOrder.ASC): '>',
    (ScrollDirection.FWD, SortOrder.DESC): '<',
    (ScrollDirection.BWD, SortOrder.ASC): '<',
    (ScrollDirection.BWD, SortOrder.DESC): '>',
}


def _get_operator(direction: ScrollDirection, order: SortOrder, unique=False):
    operator = _WHERE_OP[(direction, order)]
    if not unique:
        operator += '='
    return operator


class ScrollingPager(OffsetPager):
    def __init__(self, connection, page_size: int = 100, sort_columns: Optional[Iterable[SortColumnDefinition]] = None):
        super().__init__(connection, page_size)

        self._sort_columns: list[tuple[str, SortOrder]] = []
        self._id_column = ('rowid', SortOrder.ASC)
        if sort_columns:
            self.set_sort_columns(sort_columns)
        # Keeps track of the resultset bounds after each query
        self._cursor = {
            'first': {},
            'last': {}
        }

    def get_sort_columns(self):
        return self._sort_columns[:]

    def set_sort_columns(self, columns: Iterable[SortColumnDefinition]):
        """
        columns: [
            (name, order [, unique]),
            ...
        ]
        """
        self._sort_columns = []
        self._id_column = None
        for name, order, *rest in columns:
            unique = rest and rest[0]
            if unique:
                if self._id_column:
                    raise RuntimeError('You can add only one unique sort column.')
                self._id_column = (name, order)
                continue
            self._sort_columns.append((name, order))
        if not self._id_column:
            raise RuntimeError('You must add an unique sort column. Consider adding ("rowid", "ASC", True)')

    def execute(self, params=(), count_params=()):
        if not self._id_column:
            raise RuntimeError('You must call set_sort_columns before execute.')
        super().execute(params, count_params)
        return self

    def get_page(self, page):
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
        self._update_cursor(rs)
        return rs

    def first(self):
        self._check_executed()
        self._current_page = 1
        query, params = self._first_query, self._query_params
        rs = self._con.execute(query, params).fetchall()
        self._update_cursor(rs)
        return rs

    def last(self):
        self._check_executed()
        self._current_page = self._page_count
        query, params = self._last_query, self._query_params
        rs = self._con.execute(query, params).fetchall()
        # reverse result set
        rs.reverse()
        self._update_cursor(rs)
        return rs

    def next(self):
        self._check_executed()
        if self._current_page >= self._page_count:
            return self.last()
        self._current_page += 1
        query = self._next_fmt.format(cursor=self._cursor)
        rs = self._con.execute(query, self._query_params).fetchall()
        self._update_cursor(rs)
        return rs

    def previous(self):
        self._check_executed()
        if self._current_page <= 2:
            return self.first()
        self._current_page -= 1
        query = self._prev_fmt.format(cursor=self._cursor)
        rs = self._con.execute(query, self._query_params).fetchall()
        # reverse result set
        rs.reverse()
        self._update_cursor(rs)
        return rs

    def count(self):
        super().count()
        self._compile_queries()

    def _update_cursor(self, resultset):
        columns = self._sort_columns + [self._id_column]
        if not resultset:
            self._cursor = {
                'first': {n: None for n, _ in columns},
                'last': {n: None for n, _ in columns}
            }
            return
        for i, k in ((0, 'first'), (-1, 'last')):
            cursor = {}
            row = resultset[i]
            for name, order in columns:
                cursor[name] = row[name]
            self._cursor[k] = cursor

    def _compile_queries(self):
        fwd_orderby = self._compile_orderby_clause()
        bwd_orderby = self._compile_orderby_clause(invert=True)
        # we have to compute the number of remaining rows on the last page
        remaining_rows = self._total_size % self._page_size
        if remaining_rows == 0:
            last_page_size = self._page_size
        else:
            last_page_size = remaining_rows
        # query for self.first()
        self._first_query = f'''
            SELECT * FROM ({self._query})
            ORDER BY {fwd_orderby}
            LIMIT {self._page_size}
        '''
        # query for self.last()
        self._last_query = f'''
            SELECT * FROM ({self._query})
            ORDER BY {bwd_orderby}
            LIMIT {last_page_size}
        '''
        # query for self.next()
        self._next_fmt = f'''
            SELECT * FROM ({self._query})
            {self._precompile_where_clause(ScrollDirection.FWD)}
            ORDER BY {fwd_orderby}
            LIMIT {self._page_size}
        '''
        # query for self.previous()
        self._prev_fmt = f'''
            SELECT * FROM ({self._query})
            {self._precompile_where_clause(ScrollDirection.BWD)}
            ORDER BY {bwd_orderby}
            LIMIT {self._page_size}
        '''
        self._get_page_fmt = f'''
            SELECT * FROM ({self._query})
            ORDER BY {fwd_orderby}
            LIMIT {self._page_size} OFFSET {{offset}}
        '''

    def _compile_orderby_clause(self, invert=False):
        sort_columns = self._sort_columns + [self._id_column]
        exprs = []
        for name, order in sort_columns:
            if invert:
                order = order.reversed()
            exprs.append(f'{name} {order}')
        return ', '.join(exprs)

    def _precompile_where_clause(self, direction: ScrollDirection):
        cursor = 'last' if direction is ScrollDirection.FWD else 'first'
        comp_fmt = '{col} {op} {value}'
        value_fmt = '{cursor[%s][%s]!r}'
        # add non-unique columns
        exprs_1, exprs_2 = [], []
        for name, order in self._sort_columns:
            op1 = _get_operator(direction, order, False)
            op2 = _get_operator(direction, order, True)
            key = value_fmt % (cursor, name)
            # last_index = self._cursor[cursor][name]
            exprs_1.append(comp_fmt.format(col=name, op=op1, value=key))
            exprs_2.append(comp_fmt.format(col=name, op=op2, value=key))
        # add unique column
        name, order = self._id_column
        operator = _get_operator(direction, order, True)
        key = value_fmt % (cursor, name)
        # last_index = self._cursor[cursor][name]
        expr = comp_fmt.format(col=name, op=operator, value=key)
        if not self._sort_columns:
            return f'WHERE ({expr})'
        exprs_2.append(expr)
        return 'WHERE (({expr_1}) AND ({expr_2}))'.format(
            expr_1=' AND '.join(exprs_1),
            expr_2=' OR '.join(exprs_2)
        )

    def _is_unique_column(self, column_name: str, table_name: str):
        # PRAGMA INDEX_LIST(table_name)
        # => [{'seq': unique id of the index,
        #      'name': name of the index,
        #      'unique': nonzero if unique index
        #    }, ...]
        indexes = self._con.execute(f'pragma index_list({table_name})').fetchall()
        for idx in indexes:
            if idx['unique'] == 0:
                continue
            idx_info = self._con.execute(f'pragma index_info({idx["name"]})').fetchone()
            if idx_info['name'] == column_name:
                return True
        return False
