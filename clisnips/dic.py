from clisnips.cli.utils import UrwidMarkupHelper
from .config import Config
from .config.state import PersistentState, load_persistent_state
from .database.search_pager import SearchPager
from .database.snippets_db import SnippetsDatabase
from .stores.snippets import SnippetsStore
from .ty import AnyPath
from .utils.clock import Clock, SystemClock


class DependencyInjectionContainer:
    def __init__(self, database: AnyPath | None = None):
        self._parameters = {
            'database': database,
        }
        self._config: Config | None = None
        self._persitent_state: PersistentState | None = None
        self._database: SnippetsDatabase | None = None
        self._pager: SearchPager | None = None
        self._snippets_store: SnippetsStore | None = None
        self._clock: Clock = SystemClock()
        self._markup_helper: UrwidMarkupHelper | None = None

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

    def open_database(self, path: AnyPath | None = None) -> SnippetsDatabase:
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

    @property
    def markup_helper(self) -> UrwidMarkupHelper:
        if not self._markup_helper:
            self._markup_helper = UrwidMarkupHelper()
        return self._markup_helper
