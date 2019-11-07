import configparser
import os
import os.path
from pathlib import Path

from ._types import AnyPath

VERSION = "0.1"
AUTHORS = ['Jules Bernable (ju1ius)']
HELP_URI = 'http://github.com/ju1ius/clisnips/wiki'
LICENSE = """\
Copyright (C) 2014 {authors}

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
""".format(authors=', '.join(AUTHORS))

DEFAULTS = '''
[default]

database: ~/.config/clisnips/snippets.sqlite
sort_column: ranking
sort_order: DESC
page_size: 25

'''

HOME = Path('~').expanduser()


def xdg_config_home():
    home = os.environ.get('XDG_CONFIG_HOME')
    if not home:
        return HOME / '.config'


def xdg_config_dirs():
    dirs = (os.environ.get('XDG_CONFIG_DIRS') or '/etc/xdg').split(':')
    return [xdg_config_home()] + [Path(d) for d in dirs]


def xdg_data_home():
    home = os.environ.get('XDG_DATA_HOME')
    if not home:
        return HOME / '.local' / 'share'


def xdg_data_dirs():
    dirs = (os.environ.get('XDG_DATA_DIRS') or '/usr/local/share:/usr/share').split(':')
    return [xdg_data_home()] + [Path(d) for d in dirs]


class Config(configparser.RawConfigParser):

    def __init__(self):
        super().__init__()
        self.read_string(DEFAULTS)
        self._read_configs()

    def _read_configs(self):
        for conf_dir in reversed(xdg_config_dirs()):
            path = conf_dir / 'clisnips' / 'clisnips.ini'
            if path.exists():
                self.read(path)

    @property
    def database_path(self) -> AnyPath:
        path = self.get('default', 'database')
        if path == ':memory:':
            return path
        return Path(path).expanduser().absolute()

    @database_path.setter
    def database_path(self, value):
        self.set('default', 'database', str(value))

    @property
    def pager_sort_column(self) -> str:
        return self.get('default', 'sort_column')

    @pager_sort_column.setter
    def pager_sort_column(self, value):
        self.set('default', 'sort_column', str(value))

    @property
    def pager_sort_order(self) -> str:
        return self.get('default', 'sort_order')

    @pager_sort_order.setter
    def pager_sort_order(self, value: str):
        self.set('default', 'sort_order', str(value))

    @property
    def pager_page_size(self) -> int:
        return self.getint('default', 'page_size')

    @pager_page_size.setter
    def pager_page_size(self, value: int):
        self.set('default', 'page_size', str(value))

    def save(self):
        conf_dir = xdg_config_home() / 'clisnips'
        try:
            conf_dir.mkdir(parents=True, exist_ok=True)
        except OSError as why:
            raise RuntimeError(f'Could not create config directory {conf_dir}: {why}')
        with open(conf_dir / 'clisnips.ini', 'w') as fp:
            self.write(fp)
