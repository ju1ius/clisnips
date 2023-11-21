from traceback import format_exc

import urwid

from clisnips.tui.widgets.dialog import Dialog, ResponseKind
from clisnips.tui.widgets.divider import HorizontalDivider


def _format_error_message(err: Exception) -> str:
    return str(err)


def _format_stack_trace(err: Exception) -> str:
    return format_exc()


class ErrorDialog(Dialog):
    def __init__(self, parent, err: Exception):
        message = _format_error_message(err)
        details = _format_stack_trace(err)

        body = urwid.Pile(
            [
                urwid.Text(('error', message)),
                HorizontalDivider(),
                urwid.Text(('default', details)),
            ]
        )

        super().__init__(parent, body)
        self.set_actions(
            Dialog.Action('OK', ResponseKind.ACCEPT),
        )
        self._frame.focus_position = 1
        urwid.connect_signal(self, Dialog.Signals.RESPONSE, lambda *x: self.close())
