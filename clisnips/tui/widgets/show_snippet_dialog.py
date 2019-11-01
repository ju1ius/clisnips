import urwid

from .dialog import Dialog


class ShowSnippetDialog(Dialog):

    def __init__(self, parent, snippet):

        body = urwid.ListBox(urwid.SimpleListWalker([
            self._create_field('Title', snippet['title']),
            self._create_divider(),
            self._create_field('Tags', snippet['tag']),
            self._create_divider(),
            self._create_field('Command', snippet['cmd']),
            self._create_divider(),
            self._create_field('Documentation', snippet['doc']),
            # self._create_divider(),
        ]))

        super().__init__(parent, body)

    def _create_field(self, label, content):
        field = urwid.Pile([
            urwid.Text(label),
            urwid.Text(content),
        ])
        return field

    def _create_divider(self):
        return urwid.Divider('─')
