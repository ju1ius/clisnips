import os
import sys

import urwid
from urwid.util import decompose_tagmarkup

from clisnips.tui.urwid_types import TextMarkup


class UrwidMarkupHelper:

    palette = {
        'default': ('default', 'default'),
        'accent': ('dark magenta', 'default'),
        'accent:inverse': ('black', 'dark magenta'),
        'success': ('dark green', 'default'),
        'success:inverse': ('black', 'dark green'),
        'error': ('dark red', 'default'),
        'error:inverse': ('black', 'dark red'),
        'warning': ('brown', 'default'),
        'warning:inverse': ('black', 'brown'),
        'info': ('dark blue', 'default'),
        'info:inverse': ('white', 'dark blue'),
        'debug': ('light cyan', 'default'),
        'debug:inverse': ('black', 'light cyan'),
    }

    def __init__(self):
        self._screen = urwid.raw_display.Screen(input=os.devnull, output=os.devnull)
        self._palette_escapes = {}
        for name, attrs in self.palette.items():
            escape = self._convert_attr_spec(urwid.AttrSpec(*attrs))
            self._palette_escapes[name] = escape
        self._palette_escapes[None] = self._palette_escapes['default']

    def print(self, *args, stderr: bool = False, end: str = '\n', sep: str = ' '):
        stream = sys.stderr if stderr else sys.stdout
        tty = os.isatty(stream.fileno())
        output = sep.join(self.convert_markup(m, tty) for m in args)
        output += self.reset(tty)
        print(output, end=end, file=stream)

    def convert_markup(self, markup: TextMarkup, tty=True) -> str:
        text, attributes = decompose_tagmarkup(markup)
        if not tty:
            return text
        pos, output = 0, []
        for attr, length in attributes:
            try:
                escape = self._palette_escapes[attr]
            except KeyError:
                escape = self._palette_escapes['default']
            chunk = text[pos:pos + length]
            output.append(f'{escape}{chunk}')
            pos += length
        return ''.join(output)

    def reset(self, tty=True) -> str:
        return tty and self.convert_markup(('default', ''), tty=tty) or ''

    def _convert_attr_spec(self, attr_spec: urwid.AttrSpec) -> str:
        # noinspection PyProtectedMember
        return self._screen._attrspec_to_escape(attr_spec)
