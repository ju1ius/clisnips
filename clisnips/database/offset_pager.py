from __future__ import division
import math

import gobject


class OffsetPager(object):

    def __init__(self, connection, page_size=100):
        """
        
        """
        self._con = connection
        self._current_page = 1
        self._num_pages = 1
        self._page_size = page_size
        self._total_size = 0
        self._query = None
        self._query_params = ()
        self._count_query = None
        self._count_query_params = None

        self._executed = False

    @property
    def current_page(self):
        self._check_executed()
        return self._current_page

    @property
    def is_first_page(self):
        self._check_executed()
        return self._current_page == 1

    @property
    def is_last_page(self):
        self._check_executed()
        return self._current_page == self._num_pages

    @property
    def must_paginate(self):
        self._check_executed()
        return self._num_pages > 1

    @property
    def total_rows(self):
        return self._total_size

    def set_query(self, query, params=()):
        self._executed = False
        self._query = query
        self._query_params = params
        return self

    def get_query(self):
        return self._query

    def set_count_query(self, query, params=()):
        self._executed = False
        self._count_query = 'SELECT COUNT(*) FROM (%s)' % query
        self._count_query_params = params
        return self

    def set_page_size(self, size):
        self._executed = False
        self._page_size = size

    def execute(self, params=(), count_params=()):
        if not self._query:
            raise RuntimeError('You must call set_query before execute')
        if params:
            self._query_params = params
        if count_params:
            self._count_query_params = count_params
        self._count()
        self._executed = True
        return self

    def get_page(self, page):
        self._check_executed()
        if page <= 1:
            page = 1
        elif page >= self._num_pages:
            page = self._num_pages
        self._current_page = page
        offset = (page - 1) * self._page_size
        query = 'SELECT * FROM ({query}) LIMIT {page_size} {offset}'.format(
            query=self._query,
            page_size=self._page_size,
            offset='' if page == 1 else 'OFFSET %s' % offset
        )
        cursor = self._con.execute(query, self._query_params)
        return cursor.fetchall()

    def first(self):
        return self.get_page(1)

    def last(self):
        return self.get_page(self._num_pages)

    def next(self):
        return self.get_page(self._current_page + 1)

    def previous(self):
        return self.get_page(self._current_page - 1)

    def __len__(self):
        return self._num_pages

    def _count(self):
        if not self._count_query:
            query = 'SELECT COUNT(*) FROM (%s)' % self._query
            params = self._query_params
        else:
            query = self._count_query
            params = self._count_query_params
        count = self._con.execute(query, params).fetchone()[0]
        self._total_size = count
        self._num_pages = int(math.ceil(count / self._page_size))

    def _check_executed(self):
        if not self._executed:
            raise RuntimeError('You must execute the pager first.')
