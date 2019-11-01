from typing import Callable

import urwid

from ..dialog import Dialog, ResponseType


class EditSnippetDialog(Dialog):

    def __init__(self, parent, snippet):
        self._snippet = dict(snippet)
        self._fields = {}

        body = urwid.ListBox(urwid.SimpleListWalker([
            self._create_field('title', 'Title'),
            self._create_divider(),
            self._create_field('tag', 'Tags'),
            self._create_divider(),
            self._create_field('cmd', 'Command', multiline=True),
            self._create_divider(),
            self._create_field('doc', 'Documentation', multiline=True),
            # self._create_divider(),
        ]))

        super().__init__(parent, body)
        self.set_buttons([
            ('Cancel', ResponseType.REJECT),
            ('Apply', ResponseType.ACCEPT),
        ])
        urwid.connect_signal(self, self.Signals.RESPONSE, self._on_response)

    def on_accept(self, callback: Callable, *args):
        def handler(dialog, response_type):
            if response_type == ResponseType.ACCEPT:
                snippet = self._collect_values()
                callback(snippet)
        urwid.connect_signal(self, self.Signals.RESPONSE, handler)

    def _on_response(self, dialog, response_type):
        if response_type == ResponseType.REJECT:
            self._parent.close_dialog()

    def _collect_values(self):
        snippet = dict(self._snippet)
        values = {name: entry.get_edit_text() for name, entry in self._fields.items()}
        snippet.update(values)
        return snippet

    def _create_field(self, name, label, multiline=False):
        value = self._snippet[name]
        entry = urwid.Edit(edit_text=value, multiline=multiline)
        self._fields[name] = entry
        return urwid.Pile([
            urwid.Text(label),
            entry,
        ])

    def _create_divider(self):
        return urwid.Divider('─')
