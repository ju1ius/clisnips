import urwid

from clisnips.tui.widgets.dialog import Dialog, ResponseKind

SHORTCUTS = (
    ('F1', 'Help'),
    ('F2', 'Snippet list options'),
    ('q', 'Quit'),
    ('ESC', 'Quit or close current dialog.'),
    ('/', 'Focus search input'),
    ('Tab, Shift+Tab', 'Cycle focus between search input and snippet list.'),
    ('UP, DOWN', 'Navigate between fields.'),
    ('ENTER', 'Insert selected snippet in terminal.'),
    ('n', 'Go to next result page'),
    ('p', 'Go to previous result page'),
    ('f', 'Go to first result page'),
    ('l', 'Go to last result page'),
    ('e', 'Edit selected snippet'),
    ('+, i, INS', 'Create new snippet'),
    ('-, d, DEL', 'Delete selected snippet'),
    ('s', 'Show details for selected snippet'),
)


def _get_key_column_width():
    key, desc = max(SHORTCUTS, key=lambda x: len(x[0]))
    return len(key)


class HelpDialog(Dialog):
    def __init__(self, parent):
        body = []
        key_width = _get_key_column_width()
        for key, desc in SHORTCUTS:
            cols = urwid.Columns(
                [
                    (key_width, urwid.Text(('help:key', key))),
                    ('pack', urwid.Text(desc)),
                ],
                1,
            )
            body.append(('pack', cols))

        body = urwid.Pile(body, 0)

        super().__init__(parent, body)
        self.set_actions(
            Dialog.Action('OK', ResponseKind.ACCEPT, Dialog.Action.Kind.SUGGESTED),
        )
        self._frame.focus_position = 1
        urwid.connect_signal(self, Dialog.Signals.RESPONSE, lambda *x: self.close())
