import logging
from collections.abc import Callable
from typing import Any

import urwid

from clisnips.syntax.command.nodes import CommandTemplate
from clisnips.syntax.command.renderer import Renderer
from clisnips.syntax.documentation import Documentation
from clisnips.tui.urwid_types import TextMarkup
from clisnips.tui.widgets.dialog import Dialog, ResponseKind
from clisnips.tui.widgets.divider import HorizontalDivider
from clisnips.tui.widgets.field import Field, field_from_documentation
from clisnips.utils.iterable import intersperse

logger = logging.getLogger(__name__)


class InsertSnippetDialog(Dialog):
    def __init__(self, parent, title: str, cmd: CommandTemplate, doc: Documentation):
        self._template = cmd
        self._doc = doc
        self._renderer = Renderer()
        self._fields = self._create_fields(self._template, self._doc)

        fields = intersperse(HorizontalDivider(), self._fields.values())
        self._output = OutputField()

        body = urwid.ListBox(
            urwid.SimpleFocusListWalker(
                (
                    urwid.Pile(
                        (
                            urwid.Text(title),
                            urwid.Text(self._doc.header.strip()),
                        ),
                    ),
                    HorizontalDivider(),
                    urwid.Pile(fields),  # type: ignore (yes, fields are widgets...)
                    HorizontalDivider(),
                    self._output,
                ),
            ),
        )

        super().__init__(parent, body)
        self._apply_action = Dialog.Action('Apply', ResponseKind.ACCEPT, kind=Dialog.Action.Kind.SUGGESTED)
        self.set_actions(
            self._apply_action,
            Dialog.Action('Cancel', ResponseKind.REJECT),
        )
        self._action_area.focus_position = 1
        urwid.connect_signal(self, Dialog.Signals.RESPONSE, lambda *_: self.close())
        self._update_output()

    def on_accept(self, callback: Callable[[str], None]):
        def handler(dialog, response_type):
            if response_type == ResponseKind.ACCEPT:
                callback(self._output.get_text())

        urwid.connect_signal(self, Dialog.Signals.RESPONSE, handler)

    def _create_fields(self, command: CommandTemplate, documentation: Documentation) -> dict[str, Field[object]]:
        fields = {}
        for name in command.field_names:
            field = field_from_documentation(name, documentation)
            urwid.connect_signal(field, 'changed', lambda *_: self._update_output())
            fields[name] = field
        return fields

    def _update_output(self):
        context = {n: f.get_value() for n, f in self._fields.items()}
        try:
            context = self._apply_code_blocks(context)
            self._output.set_error_markup('')
        except Exception as err:
            self._output.set_error_markup(str(err))
            self._apply_action.disable()
            return

        output, errors = self._renderer.try_render_markup(self._template, context)
        if errors:
            self._apply_action.disable()
            for err in errors:
                field = self._fields[err.field.name]
                field.set_validation_markup(('error', str(err)))
        else:
            self._apply_action.enable()
            for field in self._fields.values():
                field.set_validation_markup('')

        self._output.set_markup(output)

    def _apply_code_blocks(self, field_values: dict[str, Any]):
        context = self._doc.execute_code({'fields': field_values})
        return context.get('fields', field_values)


class OutputField(urwid.Pile):
    def __init__(self):
        self._output = urwid.Text('')
        self._errors = urwid.Text('')
        super().__init__(
            [
                urwid.Text('Output:'),
                urwid.AttrMap(self._output, {'text': 'syn:cmd:default', 'field': 'syn:cmd:field-name'}),
                urwid.AttrMap(self._errors, 'error'),
            ]
        )

    def set_markup(self, markup: TextMarkup):
        self._output.set_text(markup)

    def get_text(self) -> str:
        text, attrs = self._output.get_text()
        return str(text)

    def set_error_markup(self, markup: TextMarkup):
        self._errors.set_text(markup)
