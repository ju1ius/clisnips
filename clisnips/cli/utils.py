import os

import urwid
from urwid.util import decompose_tagmarkup

from ..tui.urwid_types import TextMarkup


class UrwidMarkupHelper:

    palette = {
        'default': ('default', 'default'),
        'success': ('dark green', 'default'),
        'success:inverse': ('black', 'dark green'),
        'error': ('dark red', 'default'),
        'error:inverse': ('black', 'dark red'),
        'warning': ('brown', 'default'),
        'warning:inverse': ('black', 'brown'),
        'info': ('dark blue', 'default'),
        'info:inverse': ('white', 'dark blue'),
    }

    def __init__(self):
        self._screen = urwid.raw_display.Screen(input=os.devnull, output=os.devnull)
        self._palette_escapes = {}
        for name, attrs in self.palette.items():
            escape = self._convert_attr_spec(urwid.AttrSpec(*attrs))
            self._palette_escapes[name] = escape
        self._palette_escapes[None] = self._palette_escapes['default']

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
            text_part = text[pos:pos + length]
            output.append(f'{escape}{text_part}')
            pos += length
        return ''.join(output)

    def _convert_attr_spec(self, attr_spec: urwid.AttrSpec) -> str:
        return self._screen._attrspec_to_escape(attr_spec)
