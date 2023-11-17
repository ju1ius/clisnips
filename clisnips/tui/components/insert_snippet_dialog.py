from collections.abc import Callable

import urwid

from clisnips.syntax.command import parse as parse_command
from clisnips.syntax.command.nodes import CommandTemplate
from clisnips.syntax.documentation import Documentation, parse as parse_documentation
from clisnips.tui.urwid_types import TextMarkup
from clisnips.tui.widgets.dialog import Dialog, ResponseType
from clisnips.tui.widgets.divider import HorizontalDivider
from clisnips.tui.widgets.field import Field, field_from_documentation
from clisnips.utils.iterable import intersperse


class InsertSnippetDialog(Dialog):

    def __init__(self, parent, snippet):
        self._command = parse_command(snippet['cmd'])
        self._doc = parse_documentation(snippet['doc'])
        self._fields = self._create_fields(self._command, self._doc)

        title = urwid.Text(snippet['title'])
        doc_text = urwid.Text('')
        if self._doc.header:
            doc_text.set_text(self._doc.header.strip())
        self._output_text = urwid.Text('')
        self._update_output(silent=True)

        fields = intersperse(HorizontalDivider(), self._fields.values())

        output_field = urwid.Pile([
            HorizontalDivider(),
            urwid.Text('Output:'),
            urwid.AttrMap(self._output_text, 'cmd:default'),
        ])

        body = urwid.ListBox(urwid.SimpleFocusListWalker([
            urwid.Pile([
                title,
                doc_text,
                HorizontalDivider(),
            ]),
            urwid.Pile(fields),
            output_field,
        ]))

        super().__init__(parent, body)
        self.set_actions(
            Dialog.Action('Apply', ResponseType.ACCEPT, 'action:suggested'),
            Dialog.Action('Cancel', ResponseType.REJECT),
        )
        self._action_area.focus_position = 1
        urwid.connect_signal(self, Dialog.Signals.RESPONSE, self._on_response)

    def get_output(self):
        text, attrs = self._output_text.get_text()
        return text

    def on_accept(self, callback: Callable, *args):
        def handler(dialog, response_type):
            if response_type == ResponseType.ACCEPT:
                if self._validate():
                    callback(self.get_output(), *args)
                    self.close()
        urwid.connect_signal(self, Dialog.Signals.RESPONSE, handler)

    def _on_response(self, dialog, response_type, *args):
        if response_type == ResponseType.REJECT:
            self.close()

    def _on_field_changed(self, field):
        self._update_output(silent=True)

    def _create_fields(self, command: CommandTemplate, documentation: Documentation) -> dict[str, Field]:
        fields = {}
        for name in command.field_names:
            field = field_from_documentation(name, documentation)
            urwid.connect_signal(field, 'changed', self._on_field_changed)
            fields[name] = field
        return fields

    def _update_output(self, silent=False):
        fields = self._get_field_values(silent)
        output = self._get_output_markup(fields)
        self._output_text.set_text(output)

    def _get_field_values(self, silent=False):
        fields = {n: f.get_value() for n, f in self._fields.items()}
        return self._apply_code_blocks(fields, silent)

    def _apply_code_blocks(self, field_values, silent=False):
        context = {'fields': field_values}
        try:
            context = self._doc.execute_code(context)
        except Exception:
            if silent:
                return field_values
            else:
                raise
        return context['fields'] or field_values

    def _validate(self):
        try:
            self._update_output(silent=False)
        except Exception:
            # TODO: show error message
            return False
        return True

    def _get_output_markup(self, fields) -> TextMarkup:
        markup = []
        for is_field, value in self._command.apply(fields):
            match is_field, value:
                case _, '':
                    continue
                case True, _:
                    markup.append(('syn:cmd:field-name', value))
                case False, _:
                    markup.append(('syn:cmd:default', value))
        return markup
