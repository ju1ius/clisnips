import configparser
from pathlib import Path

from clisnips._types import AnyPath
from clisnips.database import SortColumn, SortOrder
from .envs import DB_PATH
from .paths import get_config_path, get_data_path
from .state import load_persistent_state, save_persistent_state

VERSION = "0.1"
AUTHORS = ['Jules Bernable (ju1ius)']
HELP_URI = 'https://github.com/ju1ius/clisnips/wiki'
LICENSE = """\
Copyright (C) {authors}

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
""".format(authors=', '.join(AUTHORS))


def _parse_ini() -> configparser.ConfigParser:
    cfg = configparser.ConfigParser(
        {'database': str(get_data_path('snippets.sqlite'))},
        default_section='default',
    )
    match get_config_path('clisnips.ini'):
        case p if p.exists(): cfg.read(p)
        case _: ...
    return cfg


class Config:

    def __init__(self):
        self._ini = _parse_ini()
        self._state = load_persistent_state()

    @property
    def database_path(self) -> AnyPath:
        if DB_PATH is not None:
            return DB_PATH
        path = self._ini.get('default', 'database')
        if path == ':memory:':
            return path
        return Path(path).expanduser().absolute()

    @property
    def pager_sort_column(self) -> SortColumn:
        return self._state['sort_by']

    @pager_sort_column.setter
    def pager_sort_column(self, value: SortColumn):
        self._state['sort_by'] = value

    @property
    def pager_sort_order(self) -> SortOrder:
        return self._state['sort_order']

    @pager_sort_order.setter
    def pager_sort_order(self, value: SortOrder):
        self._state['sort_order'] = value

    @property
    def pager_page_size(self) -> int:
        return self._state['page_size']

    @pager_page_size.setter
    def pager_page_size(self, value: int):
        self._state['page_size'] = value

    def save(self):
        save_persistent_state(self._state)
