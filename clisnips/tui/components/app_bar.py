import urwid

from clisnips.stores.snippets import SnippetsStore


class KeyBinding(urwid.Text):
    def __init__(self, key: str, label: str) -> None:
        super().__init__(
            [
                ('help:key', key),
                ('view:default', f': {label}'),
            ]
        )


class AppBar(urwid.WidgetWrap):
    def __init__(self, store: SnippetsStore):
        left = urwid.Columns(
            (
                ('pack', KeyBinding('F1', 'Help')),
                ('pack', KeyBinding('F2', 'Options')),
            ),
            dividechars=1,
        )
        sections = urwid.Columns(
            (
                left,
                ('pack', KeyBinding('ESC', 'Quit')),
            ),
            dividechars=1,
        )
        super().__init__(sections)
