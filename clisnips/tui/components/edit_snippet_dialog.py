import logging
from collections.abc import Callable
from typing import Generic, TypeVar

import urwid

from clisnips.database import NewSnippet, Snippet
from clisnips.exceptions import ParsingError
from clisnips.tui.syntax import highlight_command, highlight_documentation
from clisnips.tui.widgets.dialog import Dialog, ResponseType
from clisnips.tui.widgets.divider import HorizontalDivider
from clisnips.tui.widgets.edit import EmacsEdit, SourceEdit

S = TypeVar('S', Snippet, NewSnippet)


class EditSnippetDialog(Dialog, Generic[S]):

    def __init__(self, parent, snippet: S):
        self._snippet = snippet
        logging.getLogger(__name__).debug('snippet: %r', self._snippet)
        self._fields = {}

        body = urwid.ListBox(urwid.SimpleListWalker([
            self._create_field('title', 'Title'),
            HorizontalDivider(),
            self._create_field('tag', 'Tags'),
            HorizontalDivider(),
            self._create_field('cmd', 'Command', factory=self._command_factory),
            HorizontalDivider(),
            self._create_field('doc', 'Documentation', factory=self._documentation_factory),
        ]))

        super().__init__(parent, body)
        self.set_actions(
            Dialog.Action('Cancel', ResponseType.REJECT),
            Dialog.Action('Apply', ResponseType.ACCEPT, 'action:suggested'),
        )
        urwid.connect_signal(self, Dialog.Signals.RESPONSE, self._on_response)

    def on_accept(self, callback: Callable[[S], None], *args):
        def handler(dialog, response_type):
            if response_type == ResponseType.ACCEPT:
                snippet = self._collect_values()
                logging.getLogger(__name__).debug('accept: %r', snippet)
                callback(snippet)
        urwid.connect_signal(self, Dialog.Signals.RESPONSE, handler)

    def _on_response(self, dialog, response_type):
        if response_type == ResponseType.ACCEPT:
            # TODO: validation
            ...
        self.close()

    def _collect_values(self) -> S:
        values = {name: entry.get_edit_text() for name, entry in self._fields.items()}
        return {**self._snippet, **values} # type: ignore

    def _create_field(self, name: str, label: str, multiline=False, factory=None):
        value = self._snippet[name]
        if callable(factory):
            entry = factory(edit_text=value)
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

    def _on_command_changed(self, entry, text):
        markup = highlight_command(text)
        entry.set_edit_markup(markup)

    def _on_documentation_changed(self, entry, text):
        markup = highlight_documentation(text)
        entry.set_edit_markup(markup)
