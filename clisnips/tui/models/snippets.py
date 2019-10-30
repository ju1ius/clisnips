from ...database.snippets_db import SnippetsDatabase
from ...database.search_pager import SearchPager


class Snippets:

    def __init__(self, db: SnippetsDatabase):
        self._db = db
        self._pager = SearchPager(db, page_size=50)
