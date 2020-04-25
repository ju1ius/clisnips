from traceback import format_exc

import urwid

from clisnips.tui.widgets.dialog import Dialog, ResponseType
from clisnips.tui.widgets.divider import HorizontalDivider


class ErrorDialog(Dialog):

    def __init__(self, parent, err: Exception):
        message = self._format_error_message(err)
        details = self._format_stack_trace(err)
        # body = urwid.Filler(urwid.Padding(text, width='pack', align='center'), valign='middle')

        body = urwid.Pile([
            urwid.Text(('error', message)),
            HorizontalDivider(),
            urwid.Text(('error', details)),
        ])

        super().__init__(parent, body)
        self.set_buttons((
            ('OK', ResponseType.ACCEPT),
        ))
        self._frame.focus_position = 1
        urwid.connect_signal(self, self.Signals.RESPONSE, lambda *x: self._parent.close_dialog())

    def _format_error_message(self, err: Exception) -> str:
        return str(err)

    def _format_stack_trace(self, err: Exception) -> str:
        return format_exc()
