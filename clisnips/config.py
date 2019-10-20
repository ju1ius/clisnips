import os
import os.path
import configparser
from .utils import (
    parse_font,
    parse_color,
    get_contrast_fgcolor,
    interpolate_colors
)

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
[Default]
font: monospace 10
bg_color: #282c34
fg_color: #abb2bf
cursor_color: yellow

[Database]
path: ~/.config/clisnips/snippets.sqlite

[Pager]
sort_column: ranking
page_size: 100

'''

# TODO: fetch these from CSS
_DIFF_INS_BG_BASE = '#2ba143'  # green
_DIFF_DEL_BG_BASE = '#d13b2e'  # red

HOME = os.path.expanduser('~')

XDG_CONFIG_HOME = (os.environ.get('XDG_CONFIG_HOME')
                   or os.path.join(HOME, '.config'))
XDG_CONFIG_DIRS = ([XDG_CONFIG_HOME]
                   + (os.environ.get('XDG_CONFIG_DIRS')
                   or '/etc/xdg').split(':'))

XDG_DATA_HOME = (os.environ.get('XDG_DATA_HOME')
                 or os.path.join(HOME, '.local', 'share'))
XDG_DATA_DIRS = ([XDG_DATA_HOME]
                 + (os.environ.get('XDG_DATA_DIRS')
                    or '/usr/local/share:/usr/share').split(':'))


class _Styles(object):

    def __init__(self):
        self._font = 'monospace 10'
        self._bgcolor = parse_color('#282c34')
        self._fgcolor = parse_color('#abb2bf')
        self._cursor_color = parse_color('yellow')

    @property
    def font(self):
        return self._font

    @font.setter
    def font(self, value):
        self._font = parse_font(value)

    @property
    def diff_insert_bg(self):
        fg = get_contrast_fgcolor(self._bgcolor)
        return interpolate_colors(_DIFF_INS_BG_BASE, fg, 0.33)

    @property
    def diff_insert_fg(self):
        return get_contrast_fgcolor(self.diff_insert_bg)

    @property
    def diff_delete_bg(self):
        fg = get_contrast_fgcolor(self._bgcolor)
        return interpolate_colors(_DIFF_DEL_BG_BASE, fg, 0.33)

    @property
    def diff_delete_fg(self):
        return get_contrast_fgcolor(self.diff_delete_bg)


for pub in ('bgcolor', 'fgcolor', 'cursor_color'):

    def _prop():
        priv = '_' + pub

        def fget(self):
            return getattr(self, priv)

        def fset(self, value):
            setattr(self, priv, parse_color(value))

        return {'fget': fget, 'fset': fset}

    setattr(_Styles, pub, property(**_prop()))

del pub, _prop

styles = _Styles()


class _Parser(configparser.RawConfigParser, object):

    def __init__(self):
        super().__init__()
        self.read_string(DEFAULTS)
        self._read_configs()

    def _read_configs(self):
        for confdir in reversed(XDG_CONFIG_DIRS):
            path = os.path.join(confdir, 'clisnips', 'clisnips.conf')
            if os.path.exists(path):
                self.read(path)

    @property
    def database_path(self):
        path = self.get('Database', 'path')
        if path == ':memory:':
            return path
        return os.path.abspath(os.path.expanduser(path))

    @database_path.setter
    def database_path(self, value):
        if value != ':memory:':
            value = os.path.abspath(os.path.expanduser(value))
        self.set('Database', 'path', value)

    @property
    def pager_sort_column(self):
        return self.get('Pager', 'sort_column')

    @pager_sort_column.setter
    def pager_sort_column(self, value):
        self.set('Pager', 'sort_column', str(value))

    @property
    def pager_page_size(self):
        return self.getint('Pager', 'page_size')

    @pager_page_size.setter
    def pager_page_size(self, value):
        self.set('Pager', 'page_size', str(value))

    def save(self):
        confdir = os.path.join(XDG_CONFIG_HOME, 'clisnips')
        if not os.path.isdir(confdir):
            try:
                os.makedirs(confdir)
            except OSError as why:
                raise RuntimeError(f'Could not create config directory {confdir}: {why}')
        with open(os.path.join(confdir, 'clisnips.conf'), 'w') as fp:
            self.write(fp)


pager = {
    'sort_column': 'ranking',
    'page_size': 100
}

database_path = None

config = _Parser()
