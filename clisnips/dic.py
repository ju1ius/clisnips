import logging
from typing import Optional


from .ty import AnyPath
from .config import Config
from .config.state import PersistentState, load_persistent_state
from .database.search_pager import SearchPager
from .database.snippets_db import SnippetsDatabase
from .stores.snippets import SnippetsStore
from .utils.clock import Clock, SystemClock


class DependencyInjectionContainer:

    def __init__(self, database=None, log_level=None):
        self._parameters = {
            'database': database,
            'log_level': log_level,
        }
        self._config: Optional[Config] = None
        self._persitent_state: Optional[PersistentState] = None
        self._database: Optional[SnippetsDatabase] = None
        self._pager: Optional[SearchPager] = None
        self._snippets_store: Optional[SnippetsStore] = None
        self._clock: Clock = SystemClock()

        self._configure_logging()

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
            state = SnippetsStore.default_state()
            state.update(self.persistent_state)
            self._snippets_store = SnippetsStore(state, self.database, self.pager, self._clock)
        return self._snippets_store

    @property
    def pager(self):
        if not self._pager:
            self._pager = SearchPager(self.database)
        return self._pager

    @property
    def persistent_state(self) -> PersistentState:
        if not self._persitent_state:
            self._persitent_state = load_persistent_state()
        return self._persitent_state

    def _configure_logging(self):
        level = self._parameters.get('log_level')
        match level:
            case None | '':
                logging.basicConfig(handlers=(logging.NullHandler(),))
            case _:
                from logging.handlers import SocketHandler
                handler = SocketHandler(str(self.config.log_file), None)
                logging.basicConfig(level=level.upper(), handlers=(handler,))
