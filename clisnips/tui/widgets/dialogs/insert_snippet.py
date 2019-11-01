import string
from typing import Dict, Callable

import urwid

from ..dialog import Dialog, ResponseType
from ..field import field_from_documentation
from ..field.field import Field
from ....strfmt import doc_parser, fmt_parser
from ....strfmt.doc_nodes import Documentation
from ....utils import iterable


class InsertSnippetDialog(Dialog):

    def __init__(self, parent, snippet):
        self._command = snippet['cmd']
        self._doc = doc_parser.parse(snippet['doc'])
        self._fields = self._create_fields(self._command, self._doc)

        title = urwid.Text(snippet['title'])
        doc_text = urwid.Text('')
        if self._doc.header:
            doc_text.set_text(self._doc.header.strip())
        self._output_text = urwid.Text('')
        self._update_output()

        fields = list(iterable.join(urwid.Divider('─'), self._fields.values()))

        output_field = urwid.Pile([
            urwid.Divider('─'),
            urwid.Text('Output:'),
            self._output_text,
        ])

        body = urwid.ListBox(urwid.SimpleFocusListWalker([
            urwid.Pile([
                title,
                doc_text,
                urwid.Divider('─'),
            ]),
            urwid.Pile(fields),
            output_field,
        ]))

        super().__init__(parent, body)
        self.set_buttons((
            ('Cancel', ResponseType.REJECT),
            ('Apply', ResponseType.ACCEPT),
        ))
        self._action_area.focus_position = 1
        urwid.connect_signal(self, self.Signals.RESPONSE, self._on_response)

    def get_output(self):
        text, attrs = self._output_text.get_text()
        return text

    def on_accept(self, callback: Callable, *args):
        def handler(dialog, response_type):
            if response_type == ResponseType.ACCEPT:
                if self._accept():
                    callback(self.get_output(), *args)
                    self._parent.close_dialog()
        urwid.connect_signal(self, self.Signals.RESPONSE, handler)

    def _on_response(self, dialog, response_type, *args):
        if response_type == ResponseType.REJECT:
            self._parent.close_dialog()

    def _on_field_changed(self, field):
        self._update_output(silent=True)

    def _create_fields(self, command: str, documentation: Documentation) -> Dict[str, Field]:
        field_names = [f['name'] for f in fmt_parser.parse(command)]
        fields = {}
        for name in field_names:
            field = field_from_documentation(name, documentation)
            urwid.connect_signal(field, 'changed', self._on_field_changed)
            fields[name] = field
        return fields

    def _update_output(self, silent=False):
        fields = {n: f.get_value() for n, f in self._fields.items()}
        fields = self._apply_code_blocks(fields, silent)
        int_keys = sorted(k for k in fields.keys() if isinstance(k, int))
        args = [fields[k] for k in int_keys]
        kwargs = {k: v for k, v in fields.items() if not isinstance(k, int)}
        output = self._command.format(*args, **kwargs)
        #
        self._output_text.set_text(output)
        # self._update_diffs(output)

    def _apply_code_blocks(self, field_values, ignore_exceptions=False):
        _vars = {'fields': field_values.copy()}
        for code in self._doc.code_blocks:
            try:
                code.execute(_vars)
            except Exception as err:
                if ignore_exceptions:
                    return field_values
                else:
                    raise
        return _vars['fields']

    def _accept(self):
        try:
            self._update_output(silent=False)
        except:
            # TODO: show error message
            return False
        return True

    def _get_diff_string(self, command: str):
        formatter = string.Formatter()
        return ''.join(f[0] for f in formatter.parse(command))
