from typing import Optional

from ._types import AnyPath
from .config import Config
from .database.search_pager import SearchPager
from .database.snippets_db import SnippetsDatabase
from .tui.models.snippets import SnippetsModel
from .stores.snippets import SnippetsStore


class DependencyInjectionContainer:

    def __init__(self, database=None):
        super().__init__()
        self._parameters = {
            'database': database,
        }
        self._config: Optional[Config] = None
        self._database: Optional[SnippetsDatabase] = None
        self._pager: Optional[SearchPager] = None
        self._list_model: Optional[SnippetsModel] = None
        self._snippets_store: Optional[SnippetsStore] = None

    @property
    def config(self) -> Config:
        if not self._config:
            self._config = Config()
        return self._config

    @property
    def database(self) -> SnippetsDatabase:
        if not self._database:
            self._database = self.open_database(self._parameters.get('database'))
        return self._database

    def open_database(self, path: Optional[AnyPath] = None) -> SnippetsDatabase:
        path = path or self.config.database_path
        return SnippetsDatabase.open(path)

    @property
    def snippets_store(self) -> SnippetsStore:
        if not self._snippets_store:
            state = {
                'search_query': '',
                'snippets_by_id': {},
                'total_rows': 0,
                'current_page': 1,
                'page_count': 1,
                'page_size': self.config.pager_page_size,
                'sort_by': self.config.pager_sort_column,
                'sort_order': self.config.pager_sort_order,
            }
            self._snippets_store = SnippetsStore(state, self.database, self.pager)
        return self._snippets_store

    @property
    def pager(self):
        if not self._pager:
            self._pager = SearchPager(self.database)
            self._pager.set_sort_column(self.config.pager_sort_column, self.config.pager_sort_order)
            self._pager.page_size = self.config.pager_page_size
        return self._pager

    @property
    def list_model(self):
        if not self._list_model:
            self._list_model = SnippetsModel(self.database, self.pager)
        return self._list_model
