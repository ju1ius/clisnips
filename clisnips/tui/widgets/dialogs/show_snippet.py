import urwid

from clisnips.tui.syntax import highlight_command, highlight_documentation
from clisnips.tui.widgets.dialog import Dialog
from clisnips.tui.widgets.divider import HorizontalDivider


class ShowSnippetDialog(Dialog):

    def __init__(self, parent, snippet):

        body = urwid.ListBox(urwid.SimpleListWalker([
            self._create_field('Title', snippet['title']),
            HorizontalDivider(),
            self._create_field('Tags', snippet['tag']),
            HorizontalDivider(),
            self._create_field('Command', highlight_command(snippet['cmd'])),
            HorizontalDivider(),
            self._create_field('Documentation', highlight_documentation(snippet['doc'])),
            # HorizontalDivider(),
        ]))

        super().__init__(parent, body)

    def _create_field(self, label, content):
        field = urwid.Pile([
            urwid.Text(label),
            urwid.Text(content),
        ])
        return field
