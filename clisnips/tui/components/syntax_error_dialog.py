from collections.abc import Callable
from textwrap import dedent

import urwid

from clisnips.tui.widgets.dialog import Dialog, ResponseKind

_MESSAGE = dedent(
    """
    There seems to be a syntax error in your snippet...
    You should probably edit it.
    """
)


class SyntaxErrorDialog(Dialog):
    def __init__(self, parent):
        text = urwid.Text(('warning', _MESSAGE))
        body = urwid.Filler(urwid.Padding(text, width='pack', align='center'), valign='middle')

        super().__init__(parent, body)
        self.set_actions(
            Dialog.Action('Edit', ResponseKind.ACCEPT, Dialog.Action.Kind.SUGGESTED),
            Dialog.Action('Cancel', ResponseKind.REJECT),
        )
        self._frame.focus_position = 1
        urwid.connect_signal(self, Dialog.Signals.RESPONSE, lambda *x: self.close())

    def on_accept(self, callback: Callable[..., None], *args):
        def handler(dialog, response_type):
            if response_type == ResponseKind.ACCEPT:
                callback(*args)

        urwid.connect_signal(self, Dialog.Signals.RESPONSE, handler)
