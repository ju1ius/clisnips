from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Generic, Self, TypeVar

import observ
import urwid

from clisnips.database import NewSnippet, Snippet
from clisnips.exceptions import ParseError
from clisnips.syntax import parse_command, parse_documentation
from clisnips.tui.highlighters import highlight_command, highlight_documentation
from clisnips.tui.loop import debounced
from clisnips.tui.urwid_types import TextMarkup
from clisnips.tui.widgets.dialog import Dialog, ResponseKind
from clisnips.tui.widgets.divider import HorizontalDivider
from clisnips.tui.widgets.edit import EmacsEdit, SourceEdit
from clisnips.utils.iterable import intersperse

S = TypeVar('S', Snippet, NewSnippet)
logger = logging.getLogger(__name__)


class EditSnippetDialog(Dialog, Generic[S]):
    def __init__(self, parent, snippet: S):
        self._snippet = snippet
        logger.debug('snippet: %r', snippet)

        self._fields = {
            'title': SimpleField('Title:', snippet['title']),
            'tag': SimpleField('Tags:', snippet['tag']),
            'cmd': ComplexField('Command:', highlight_command(snippet['cmd'])),
            'doc': ComplexField('Documentation:', highlight_documentation(snippet['doc'])),
        }
        self._fields['cmd'].on_change(self._highlight_cmd_on_changed)
        self._fields['cmd'].on_change(self._check_cmd_syntax_on_changed, now=True)
        self._fields['doc'].on_change(self._highlight_doc_on_changed)
        self._fields['doc'].on_change(self._check_doc_syntax_on_changed, now=True)

        body = urwid.ListBox(urwid.SimpleListWalker(intersperse(HorizontalDivider(), self._fields.values())))
        super().__init__(parent, body)

        self._save_action = Dialog.Action('Apply', ResponseKind.ACCEPT, Dialog.Action.Kind.SUGGESTED)
        self.set_actions(
            self._save_action,
            Dialog.Action('Cancel', ResponseKind.REJECT),
        )
        urwid.connect_signal(self, Dialog.Signals.RESPONSE, lambda *_: self.close())

        self._errors = observ.reactive(set())
        self._watchers = {
            'errors': observ.watch(self._errors, self._on_errors_changed, immediate=True),
        }

    def on_accept(self, callback: Callable[[S], None], *args):
        def handler(dialog, response_type):
            if response_type == ResponseKind.ACCEPT:
                snippet = self._collect_values()
                logger.debug('accept: %r', snippet)
                callback(snippet)

        urwid.connect_signal(self, Dialog.Signals.RESPONSE, handler)

    def _collect_values(self) -> S:
        values = {name: entry.get_edit_text() for name, entry in self._fields.items()}
        return {**self._snippet, **values}  # type: ignore

    def _highlight_cmd_on_changed(self, entry: ComplexField, text: str):
        markup = highlight_command(text)
        entry.set_edit_markup(markup)

    def _highlight_doc_on_changed(self, entry: ComplexField, text: str):
        markup = highlight_documentation(text)
        entry.set_edit_markup(markup)

    @debounced(300)
    def _check_cmd_syntax_on_changed(self, entry, value):
        template: str = entry.get_edit_text()
        try:
            _ = parse_command(template)
        except ParseError as err:
            logger.warn(str(err))
            entry.set_error_text(str(err))
            self._errors.add('cmd')
        else:
            entry.set_error_text('')
            self._errors.discard('cmd')

    @debounced(300)
    def _check_doc_syntax_on_changed(self, entry, value):
        doc: str = entry.get_edit_text()
        try:
            _ = parse_documentation(doc)
        except ParseError as err:
            logger.warn(str(err))
            entry.set_error_text(str(err))
            self._errors.add('doc')
        else:
            entry.set_error_text('')
            self._errors.discard('doc')

    def _on_errors_changed(self, errors: set[str]):
        self._save_action.toggle(not errors)


class SimpleField(urwid.Pile):
    def __init__(self, label: str, value: str):
        self._label = urwid.Text(label)
        self._entry = EmacsEdit(edit_text=value)
        super().__init__(
            [
                self._label,
                self._entry,
            ]
        )

    def get_entry(self) -> urwid.Edit:
        return self._entry

    def get_edit_text(self) -> str:
        return self._entry.get_edit_text()


class ComplexField(urwid.Pile):
    def __init__(
        self,
        label: str,
        markup: TextMarkup,
    ):
        self._label = urwid.Text(label)
        self._entry = SourceEdit(edit_text='', multiline=True)
        self._entry.set_edit_markup(markup)
        self._errors = urwid.AttrMap(urwid.Text(''), 'error')
        super().__init__(
            [
                self._label,
                self._entry,
                self._errors,
            ]
        )

    def get_entry(self) -> urwid.Edit:
        return self._entry

    def get_edit_text(self) -> str:
        return self._entry.get_edit_text()

    def set_edit_markup(self, markup: TextMarkup):
        self._entry.set_edit_markup(markup)

    def set_error_text(self, err: str):
        self._errors.original_widget.set_text(err)  # type: ignore (original_widget is a Text widget)
        try:
            self.contents.remove((self._errors, ('weight', 1)))
        except ValueError:
            ...
        if err:
            self.contents.insert(2, (self._errors, ('weight', 1)))

    def on_change(self, cb: Callable[[Self, str], None], now=False):
        urwid.connect_signal(self._entry, 'change', lambda _, v: cb(self, v))
        if now:
            cb(self, self._entry.get_edit_text())
