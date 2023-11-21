from collections.abc import Callable

import urwid

from clisnips.tui.widgets.dialog import Dialog, ResponseKind


class ConfirmDialog(Dialog):
    def __init__(self, parent, message: str = '', accept_text: str = 'Confirm', reject_text: str = 'Cancel'):
        text = urwid.Text(message)
        body = urwid.Filler(urwid.Padding(text, width='pack', align='center'), valign='middle')
        super().__init__(parent, body)
        self.set_actions(
            Dialog.Action(reject_text, ResponseKind.REJECT),
            Dialog.Action(accept_text, ResponseKind.ACCEPT),
        )
        self._frame.focus_position = 1
        urwid.connect_signal(self, Dialog.Signals.RESPONSE, lambda *x: self.close())

    def on_accept(self, callback: Callable, *args):
        def handler(dialog, response_type):
            if response_type == ResponseKind.ACCEPT:
                callback(*args)

        urwid.connect_signal(self, Dialog.Signals.RESPONSE, handler)

    def on_reject(self, callback: Callable, *args):
        def handler(dialog, response_type):
            if response_type == ResponseKind.REJECT:
                callback(*args)

        urwid.connect_signal(self, Dialog.Signals.RESPONSE, handler)
