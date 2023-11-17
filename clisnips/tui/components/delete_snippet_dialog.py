from collections.abc import Callable

import urwid
from urwid.widget.constants import Align, VAlign, WHSettings

from clisnips.tui.widgets.dialog import Dialog, ResponseType


class DeleteSnippetDialog(Dialog):

    def __init__(self, parent):
        text = urwid.Text('Are you sure you want to delete this snippet ?')
        body = urwid.Filler(urwid.Padding(text, width=WHSettings.PACK, align=Align.CENTER), valign=VAlign.MIDDLE)
        super().__init__(parent, body)

        self.set_actions(
            Dialog.Action('Cancel', ResponseType.REJECT),
            Dialog.Action('Confirm', ResponseType.ACCEPT, 'action:destructive'),
        )
        self._frame.focus_position = 1
        urwid.connect_signal(self, Dialog.Signals.RESPONSE, lambda *x: self.close())

    def on_accept(self, callback: Callable, *args):
        def handler(dialog, response_type):
            if response_type == ResponseType.ACCEPT:
                callback(*args)
        urwid.connect_signal(self, Dialog.Signals.RESPONSE, handler)
