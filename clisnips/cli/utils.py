import os
import sys

import urwid
from urwid.util import decompose_tagmarkup

from clisnips.tui.urwid_types import TextMarkup


class _DummyScreen(urwid.raw_display.Screen):
    def __init__(self):
        super().__init__(
            input=os.devnull,  # type: ignore
            output=os.devnull,  # type: ignore
            bracketed_paste_mode=False,
        )

    def convert_attr(self, spec: urwid.AttrSpec) -> str:
        return self._attrspec_to_escape(spec)  # type: ignore

    def decompose_markup(self, markup: TextMarkup) -> tuple[str, list[tuple[str, int]]]:
        return decompose_tagmarkup(markup)  # type: ignore


class UrwidMarkupHelper:
    palette = {
        'default': ('default', 'default'),
        'accent': ('dark magenta', 'default'),
        'success': ('dark green', 'default'),
        'error': ('dark red', 'default'),
        'warning': ('brown', 'default'),
        'info': ('dark blue', 'default'),
        'debug': ('dark cyan', 'default'),
    }

    def __init__(self):
        self._screen = _DummyScreen()
        self._palette_escapes: dict[str | None, str] = {}
        for name, attrs in self.palette.items():
            escape = self._screen.convert_attr(urwid.AttrSpec(*attrs))
            self._palette_escapes[name] = escape
        self._palette_escapes[None] = self._palette_escapes['default']

    def print(self, *args: TextMarkup, stderr: bool = False, end: str = '\n', sep: str = ' '):
        stream = sys.stderr if stderr else sys.stdout
        tty = stream.isatty()
        output = sep.join(self.convert_markup(m, tty) for m in args)
        output += self.reset(tty)
        print(output, end=end, file=stream)

    def convert_markup(self, markup: TextMarkup, tty: bool = True) -> str:
        text, attributes = self._screen.decompose_markup(markup)
        if not tty:
            return str(text)
        pos = 0
        output: list[str] = []
        for attr, length in attributes:
            try:
                escape = self._palette_escapes[attr]
            except KeyError:
                escape = self._palette_escapes['default']
            chunk = text[pos : pos + length]
            output.append(f'{escape}{chunk}')
            pos += length
        return ''.join(output)

    def reset(self, tty: bool = True) -> str:
        return tty and self.convert_markup(('default', ''), tty=tty) or ''
