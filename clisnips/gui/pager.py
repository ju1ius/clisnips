from ..database.scrolling_pager import ScrollingPager


class Pager(object):

    MODE_LIST = 1
    MODE_SEARCH = 2

    def __init__(self, ui, db, page_size):
        self._page_size = page_size
        self.snips_pager = ScrollingPager(db.connection, page_size)
        self.snips_pager.set_query(db.get_listing_query())
        self.snips_pager.set_count_query(db.get_listing_count_query())

        self.search_pager = ScrollingPager(db.connection, page_size)
        self.search_pager.set_query(db.get_search_query())
        self.search_pager.set_count_query(db.get_search_count_query())

        self._mode = self.MODE_LIST
        self._current_pager = self.snips_pager

        self.first_btn = ui.get_object('pager_first_btn')
        self.next_btn = ui.get_object('pager_next_btn')
        self.prev_btn = ui.get_object('pager_prev_btn')
        self.last_btn = ui.get_object('pager_last_btn')
        self.curpage_lbl = ui.get_object('pager_curpage_lbl')
        self.infos_lbl = ui.get_object('pager_info_lbl')

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        if mode == self.MODE_SEARCH:
            self._mode = self.MODE_SEARCH
            self._current_pager = self.search_pager
        else:
            self._mode = self.MODE_LIST
            self._current_pager = self.snips_pager

    @property
    def page_size(self):
        return self._page_size

    @page_size.setter
    def page_size(self, size):
        self.set_page_size(size)

    def set_sort_columns(self, columns):
        self.snips_pager.set_sort_columns(columns)
        self.search_pager.set_sort_columns(columns)

    def set_page_size(self, size):
        self._page_size = size
        self.snips_pager.set_page_size(size)
        self.search_pager.set_page_size(size)

    def execute(self, params=(), count_params=()):
        self._current_pager.execute(params, count_params)
        return self

    def first(self):
        rows = self._current_pager.first()
        self.first_btn.set_sensitive(False)
        self.prev_btn.set_sensitive(False)
        self.last_btn.set_sensitive(True)
        self.next_btn.set_sensitive(True)
        self._update_page_label()
        return rows

    def last(self):
        rows = self._current_pager.last()
        self.first_btn.set_sensitive(True)
        self.prev_btn.set_sensitive(True)
        self.last_btn.set_sensitive(False)
        self.next_btn.set_sensitive(False)
        self._update_page_label()
        return rows

    def next(self):
        rows = self._current_pager.next()
        is_last_page = self._current_pager.is_last_page
        self.first_btn.set_sensitive(True)
        self.prev_btn.set_sensitive(True)
        self.last_btn.set_sensitive(not is_last_page)
        self.next_btn.set_sensitive(not is_last_page)
        self._update_page_label()
        return rows

    def previous(self):
        rows = self._current_pager.previous()
        is_first_page = self._current_pager.is_first_page
        self.first_btn.set_sensitive(not is_first_page)
        self.prev_btn.set_sensitive(not is_first_page)
        self.last_btn.set_sensitive(True)
        self.next_btn.set_sensitive(True)
        self._update_page_label()
        return rows

    def _update_page_label(self):
        page = self._current_pager.current_page
        num_pages = len(self._current_pager)
        self.curpage_lbl.set_text(str(page))
        infos = 'page %s of %s (%s rows)' % (
            page, num_pages, self._current_pager.total_rows
        )
        self.infos_lbl.set_text(infos)
