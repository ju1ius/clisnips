from contextlib import suppress
from typing import Callable

import urwid

from ..dialog import Dialog, ResponseType
from ..divider import HorizontalDivider
from ..edit import EmacsEdit, SourceEdit
from ...syntax import highlight_command, highlight_documentation
from ....exceptions import ParsingError


class EditSnippetDialog(Dialog):

    def __init__(self, parent, snippet):
        self._snippet = dict(snippet)
        self._fields = {}

        body = urwid.ListBox(urwid.SimpleListWalker([
            self._create_field('title', 'Title'),
            HorizontalDivider(),
            self._create_field('tag', 'Tags'),
            HorizontalDivider(),
            self._create_field('cmd', 'Command', entry_factory=self._command_factory),
            HorizontalDivider(),
            self._create_field('doc', 'Documentation', entry_factory=self._documentation_factory),
            # HorizontalDivider(),
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

    def _create_field(self, name, label, multiline=False, entry_factory=None):
        value = self._snippet[name]
        if callable(entry_factory):
            entry = entry_factory(edit_text=value)
        else:
            entry = EmacsEdit(edit_text=value, multiline=multiline)
        self._fields[name] = entry
        return urwid.Pile([
            urwid.Text(label),
            entry,
        ])

    def _command_factory(self, edit_text: str):
        entry = SourceEdit(edit_text='', multiline=True)
        entry.set_edit_markup(highlight_command(edit_text))
        urwid.connect_signal(entry, 'change', self._on_command_changed)
        return entry

    def _documentation_factory(self, edit_text: str):
        entry = SourceEdit(edit_text='', multiline=True)
        entry.set_edit_markup(highlight_documentation(edit_text))
        urwid.connect_signal(entry, 'change', self._on_documentation_changed)
        return entry

    @staticmethod
    def _on_command_changed(entry, text):
        with suppress(ParsingError):
            markup = highlight_command(text)
            entry.set_edit_markup(markup)

    @staticmethod
    def _on_documentation_changed(entry, text):
        with suppress(ParsingError):
            markup = highlight_documentation(text)
            entry.set_edit_markup(markup)
