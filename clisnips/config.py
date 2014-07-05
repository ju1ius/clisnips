from .utils import (parse_font, parse_color,
                    get_contrast_fgcolor, interpolate_colors)


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


_DIFF_INS_BG_BASE = '#00FF00'  # green
_DIFF_DEL_BG_BASE = '#FF0000'  # red


class _Styles(object):

    def __init__(self):
        self._font = 'monospace 10'
        self._bgcolor = parse_color('#111')
        self._fgcolor = parse_color('#ccc')
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

pager = {
    'sort_column': 'ranking',
    'page_size': 100
}

database_path = None
