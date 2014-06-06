import os
import string

import gtk
import pango

from .. import config
from .helpers import BuildableWidgetDecorator, SimpleTextView 
from ..strfmt.doc_lexer import Lexer
from ..strfmt.doc_parser import Parser
from . import strfmt_widgets


__DIR__ = os.path.abspath(os.path.dirname(__file__))


class StringFormatterDialog(BuildableWidgetDecorator):

    UI_FILE = os.path.join(__DIR__, 'strfmt_dialog.ui')
    MAIN_WIDGET = 'main_dialog'
    WIDGET_IDS = ('title_lbl', 'format_string_lbl', 'doc_lbl',
                  'fields_vbox', 'output_edit_cb', 'output_textview')

    def __init__(self):
        super(StringFormatterDialog, self).__init__()
        self.formatter = string.Formatter()
        self.format_string = ''
        self.fields = []
        self.cwd = os.path.expanduser('~')

        font_desc = pango.FontDescription(config.font)
        self.output_textview.modify_font(font_desc)
        self.format_string_lbl.modify_font(font_desc)
        self.output_textview = SimpleTextView(self.output_textview)
        self.connect_signals()

    def set_cwd(self, cwd):
        self.cwd = cwd

        def _cb(widget):
            print widget
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
        self.format_string_lbl.set_text(self.format_string)
        self.title_lbl.set_text('')
        self.doc_lbl.set_text('')
        self.output_textview.set_text('')
        self.fields = []
        for child in self.fields_vbox.get_children():
            self.fields_vbox.remove(child)

    def add_field(self, field_name, field_doc):
        if field_doc is not None:
            doc = field_doc.text.strip()
            field_label = '<b>{name}</b> ({type})\n{doc}'.format(
                name=field_name,
                type=field_doc.typehint if field_doc.typehint else '',
                doc=doc
            )
        else:
            field_label = field_name
        vbox = gtk.VBox()
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
        self.output_textview.set_text(self.get_output())

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

    ###########################################################################
    # ------------------------------ SIGNALS
    ###########################################################################

    def on_output_edit_cb_toggled(self, widget):
        self.output_textview.set_editable(widget.get_active())

    def on_reset_btn_clicked(self, widget):
        # reset output to format string
        self.output_textview.set_text(self.format_string_lbl.get_text())
        # then update with fields contents
        self.update_preview()
    def on_field_change(self, widget):
        self.update_preview()

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
