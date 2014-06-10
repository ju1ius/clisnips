import os
import string

import gtk
import glib

from .. import config
import helpers
from ..strfmt.doc_lexer import Lexer
from ..strfmt.doc_parser import Parser
from ..diff import InlineMyersSequenceMatcher
from . import strfmt_widgets


__DIR__ = os.path.abspath(os.path.dirname(__file__))


class StringFormatterDialog(helpers.BuildableWidgetDecorator):

    UI_FILE = os.path.join(__DIR__, 'strfmt_dialog.ui')
    MAIN_WIDGET = 'main_dialog'
    WIDGET_IDS = ('title_lbl', 'doc_lbl', 'fields_vbox',
                  'fmtstr_lbl', 'fmtstr_textview',
                  'output_edit_cb', 'output_textview')
    UPDATE_TIMEOUT = 200

    def __init__(self):
        super(StringFormatterDialog, self).__init__()
        self.formatter = string.Formatter()
        self.format_string = ''
        self.fields = []
        self.cwd = os.path.expanduser('~')
        # output textview
        self.output_textview = helpers.SimpleTextView(self.output_textview)
        self.output_textview.set_font(config.font)
        self.output_textview.set_background_color(config.bgcolor)
        self.output_textview.set_text_color(config.fgcolor)
        self.output_textview.set_cursor_color(config.cursor_color)
        self.output_textview.set_padding(6)

        # format string textview
        self.fmtstr_textview = helpers.SimpleTextView(
            self.fmtstr_textview)
        self.fmtstr_textview.set_font(config.font)
        self.fmtstr_textview.set_background_color('white')
        self.fmtstr_textview.set_text_color('black')
        self.fmtstr_textview.set_padding(6)

        # diff tags
        for tv in ('output_textview', 'fmtstr_textview'):
            textview = getattr(self, tv)
            textview.create_tag('diff_insert', background='green', weight=700)
            textview.create_tag('diff_delete', background='red', weight=700)

        # signals
        self.connect_signals()
        self.handlers = {'update_timeout': 0}
        self.handlers['output_changed'] = self.output_textview.connect(
            'changed',
            self.on_output_changed
        )
        self.output_textview.handler_block(
            self.handlers['output_changed'])
        # diff
        self.differ = InlineMyersSequenceMatcher()

    def set_cwd(self, cwd):
        self.cwd = cwd

        def _cb(widget):
            if isinstance(widget, strfmt_widgets.PathEntry):
                widget.set_cwd(cwd)
        self.fields_vbox.foreach(_cb)

    def run(self, title, format_string, docstring=''):
        self.format_string = format_string
        self.reset_fields()
        self.title_lbl.set_text(title)
        field_names = self._parse_format_string(format_string)
        if not field_names:
            # no arguments, return command as is
            return gtk.RESPONSE_ACCEPT
        if not docstring:
            doc = {
                'text': '',
                'parameters': {}
            }
        else:
            doc = self._parse_docstring(docstring)
            self.doc_lbl.set_markup(doc['text'])
        if not doc['text']:
            self.doc_lbl.hide()
        self.set_fields(field_names, doc['parameters'])
        return self.widget.run()

    def set_fields(self, field_names, parameters):
        for name in field_names:
            param_doc = parameters.get(name)
            self.add_field(name, param_doc)
        self.fields_vbox.show_all()
        self.update_preview()

    def reset_fields(self):
        self.title_lbl.set_text('')
        self.doc_lbl.set_text('')
        self.fmtstr_textview.set_text(
            ''.join(f[0] for f in self.formatter.parse(self.format_string))
        )
        self.output_textview.set_text('')
        self.fields = []
        for child in self.fields_vbox.get_children():
            self.fields_vbox.remove(child)

    def add_field(self, field_name, field_doc):
        if field_doc is not None:
            doc = field_doc.text.strip()
            field_label = '<b>{name}</b> <i>({type})</i> {doc}'.format(
                name=field_name,
                type=field_doc.typehint if field_doc.typehint else '',
                doc=doc
            )
        else:
            field_label = field_name
        vbox = gtk.VBox(spacing=6)
        label = gtk.Label()
        label.set_alignment(0, 0.5)
        label.set_markup(field_label)
        entry = strfmt_widgets.from_doc_parameter(field_doc)
        entry.connect('changed', self.on_field_change)

        vbox.pack_start(label, False)
        vbox.pack_start(entry, False)
        self.fields_vbox.pack_start(vbox)

        self.fields.append({
            'name': field_name,
            'entry': entry
        })

    def get_output(self):
        args, kwargs = [], {}
        for field in self.fields:
            key = field['name']
            value = field['entry'].get_value()
            if key:
                try:
                    key = int(key)
                    args.insert(key, value)
                except ValueError:
                    kwargs[key] = value
            else:
                args.append(value)
        return self.format_string.format(*args, **kwargs)

    def update_preview(self):
        self.handlers['update_timeout'] = 0
        output = self.get_output()
        self.output_textview.set_text(output)
        self._update_diffs(output)

    def _parse_docstring(self, docstring):
        parser = Parser(Lexer(docstring))
        tree = parser.parse()
        params_dict = {}
        auto_count = -1
        has_numeric_field = False
        for param in tree.parameters:
            if param.name == '':
                if has_numeric_field:
                    raise ValueError(
                        "Cannot mix manual and automatic field numbering"
                    )
                auto_count += 1
                param.name = auto_count
            else:
                try:
                    param.name = int(param.name)
                    is_numeric = True
                    has_numeric_field = True
                except ValueError:
                    is_numeric = False
                if is_numeric and auto_count > -1:
                    raise ValueError(
                        "Cannot mix manual and automatic field numbering"
                    )
            params_dict[param.name] = param
        return {
            'text': tree.text.strip(),
            'parameters': params_dict
        }

    def _parse_format_string(self, format_string):
        fields = [
            f for f in self.formatter.parse(format_string) if f[1] is not None
        ]
        if not fields:
            return None
        field_names = []
        auto_count = -1
        has_numeric_field = False
        for field in fields:
            literal_text, field_name, format_spec, conversion = field
            if field_name == '':
                if has_numeric_field:
                    raise ValueError(
                        "Cannot mix manual and automatic field numbering"
                    )
                auto_count += 1
                field_name = auto_count
            else:
                try:
                    field_name = int(field_name)
                    is_numeric = True
                    has_numeric_field = True
                except ValueError:
                    is_numeric = False
                if is_numeric and auto_count > -1:
                    raise ValueError(
                        "Cannot mix manual and automatic field numbering"
                    )
            field_names.append(field_name)
        return field_names

    def _update_diffs(self, output):
        # clear all text tags
        ot, fst = self.output_textview, self.fmtstr_textview
        ot.remove_all_tags()
        fst.remove_all_tags()
        # compute diff
        self.differ.set_seqs(fst.get_text(), output)
        for op, start1, end1, start2, end2 in self.differ.get_opcodes():
            if op == 'equal':
                continue
            if op == 'insert':
                ot.apply_tag('diff_insert', start2, end2)
            elif op == 'delete':
                fst.apply_tag('diff_delete', start1, end1)
            elif op == 'replace':
                fst.apply_tag('diff_delete', start1, end1)
                ot.apply_tag('diff_insert', start2, end2)

    ###########################################################################
    # ------------------------------ SIGNALS
    ###########################################################################

    def on_output_edit_cb_toggled(self, widget):
        editable = widget.get_active()
        self.output_textview.set_editable(editable)
        if editable:
            self.output_textview.handler_unblock(
                self.handlers['output_changed'])
        else:
            self.output_textview.handler_block(
                self.handlers['output_changed'])

    def on_output_changed(self, widget):
        self._update_diffs(widget.get_text())

    def on_reset_btn_clicked(self, widget):
        # reset output to format string
        self.output_textview.set_text(self.fmtstr_lbl.get_text())
        # then update with fields contents
        self.update_preview()

    def on_field_change(self, widget):
        if self.handlers['update_timeout']:
            glib.source_remove(self.handlers['update_timeout'])
        self.handlers['update_timeout'] = glib.timeout_add(
            self.UPDATE_TIMEOUT,
            self.update_preview
        )

    def on_main_dialog_response(self, widget, response_id):
        if response_id == gtk.RESPONSE_ACCEPT:
            self.widget.hide()
        elif response_id == gtk.RESPONSE_REJECT:
            self.reset_fields()
            self.widget.hide()
        elif response_id == gtk.RESPONSE_DELETE_EVENT:
            self.reset_fields()
            self.widget.hide()
            return True
        return False
