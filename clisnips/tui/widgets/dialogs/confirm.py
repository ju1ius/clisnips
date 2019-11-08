from typing import Callable

import urwid

from ..dialog import Dialog, ResponseType


class ConfirmDialog(Dialog):

    def __init__(self, parent, message: str = '', accept_text: str = 'Confirm', reject_text: str = 'Cancel'):
        text = urwid.Text(message)
        body = urwid.Filler(urwid.Padding(text, width='pack', align='center'), valign='middle')
        super().__init__(parent, body)
        self.set_buttons((
            (reject_text, ResponseType.REJECT),
            (accept_text, ResponseType.ACCEPT),
        ))
        self._frame.focus_position = 1
        urwid.connect_signal(self, self.Signals.RESPONSE, lambda *x: self._parent.close_dialog())

    def on_accept(self, callback: Callable, *args):
        def handler(dialog, response_type):
            if response_type == ResponseType.ACCEPT:
                callback(*args)
        urwid.connect_signal(self, self.Signals.RESPONSE, handler)

    def on_reject(self, callback: Callable, *args):
        def handler(dialog, response_type):
            if response_type == ResponseType.REJECT:
                callback(*args)
        urwid.connect_signal(self, self.Signals.RESPONSE, handler)
