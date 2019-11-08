import string
from typing import Callable, Dict

import urwid

from clisnips.diff import InlineMyersSequenceMatcher
from clisnips.strfmt import doc_parser, fmt_parser
from clisnips.strfmt.doc_nodes import Documentation
from clisnips.tui.widgets.dialog import Dialog, ResponseType
from clisnips.tui.widgets.divider import HorizontalDivider
from clisnips.tui.widgets.field import field_from_documentation
from clisnips.tui.widgets.field.field import Field
from clisnips.utils import iterable


class InsertSnippetDialog(Dialog):

    def __init__(self, parent, snippet):
        self._command = snippet['cmd']
        self._doc = doc_parser.parse(snippet['doc'])
        self._fields = self._create_fields(self._command, self._doc)
        self._differ = InlineMyersSequenceMatcher()
        self._diff_base = self._get_diff_base(self._command)

        title = urwid.Text(snippet['title'])
        doc_text = urwid.Text('')
        if self._doc.header:
            doc_text.set_text(self._doc.header.strip())
        self._output_text = urwid.Text('')
        self._update_output()

        fields = list(iterable.join(HorizontalDivider(), self._fields.values()))

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
        field_names = [str(f['name']) for f in fmt_parser.parse(command)]
        fields = {}
        for name in field_names:
            field = field_from_documentation(name, documentation)
            urwid.connect_signal(field, 'changed', self._on_field_changed)
            fields[name] = field
        return fields

    def _update_output(self, silent=False):
        fields = {n: f.get_value() for n, f in self._fields.items()}
        fields = self._apply_code_blocks(fields, silent)
        int_keys, str_keys = [], []
        for k in fields.keys():
            if k.isdigit():
                int_keys.append(k)
            else:
                str_keys.append(k)
        args = [fields[k] for k in sorted(int_keys)]
        kwargs = {k: fields[k] for k in str_keys}
        output = self._command.format(*args, **kwargs)
        #
        output = self._get_output_markup(output)
        self._output_text.set_text(output)

    def _apply_code_blocks(self, field_values, ignore_exceptions=False):
        if not self._doc.code_blocks:
            return field_values
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

    def _get_output_markup(self, text):
        self._differ.set_seqs(self._diff_base, text)
        markup = []
        for op, start1, end1, start2, end2 in self._differ.get_opcodes():
            if op == 'equal':
                markup.append(text[start2:end2])
            elif op == 'insert':
                markup.append(('diff:insert', text[start2:end2]))
            elif op == 'delete':
                # shouldn't happen...
                pass
            elif op == 'replace':
                # shouldn't happen either but left for completeness
                markup.append(('diff:insert', text[start2:end2]))
        return markup

    @staticmethod
    def _get_diff_base(command: str):
        formatter = string.Formatter()
        return ''.join(f[0] for f in formatter.parse(command))
