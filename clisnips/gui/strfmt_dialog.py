import os
import string
from collections import OrderedDict

import gtk
import glib

from ..config import styles
from .state import State
from .helpers import BuildableWidgetDecorator, SimpleTextView
from ..strfmt import doc_parser 
from ..strfmt import fmt_parser 
from ..strfmt.doc_tokens import T_PARAM
from ..diff import InlineMyersSequenceMatcher
from .strfmt_widgets import Field, PathEntry 


__DIR__ = os.path.abspath(os.path.dirname(__file__))


class StrfmtDialogState(State):
    NORMAL_EDITING = 0x01
    DIRECT_EDITING = 0x02


class StringFormatterDialog(BuildableWidgetDecorator):

    UI_FILE = os.path.join(__DIR__, 'strfmt_dialog.ui')
    MAIN_WIDGET = 'main_dialog'
    WIDGET_IDS = ('title_lbl', 'doc_lbl', 'fields_vbox',
                  'fmtstr_lbl', 'fmtstr_textview',
                  'output_edit_cb', 'output_textview')
    UPDATE_TIMEOUT = 200

    def __init__(self):
        super(StringFormatterDialog, self).__init__()
        self.formatter = string.Formatter()
        # the original format string
        self.format_string = ''
        # the string used for diffing and advanced editing
        self.diff_string = ''
        self.fields = OrderedDict()
        self.cwd = os.path.expanduser('~')
        # state manager
        self.state = StrfmtDialogState()
        self.state.connect('enter-state', self.on_enter_state)
        self.state.connect('leave-state', self.on_leave_state)

        # output textview
        self.output_textview = SimpleTextView(self.output_textview)
        self.output_textview.set_font(styles.font)
        self.output_textview.set_background_color(styles.bgcolor)
        self.output_textview.set_text_color(styles.fgcolor)
        self.output_textview.set_cursor_color(styles.cursor_color)
        self.output_textview.set_padding(6)

        # format string textview
        self.fmtstr_textview = SimpleTextView(self.fmtstr_textview)
        self.fmtstr_textview.set_font(styles.font)
        self.fmtstr_textview.set_background_color('white')
        self.fmtstr_textview.set_text_color('black')
        self.fmtstr_textview.set_padding(6)

        # diff tags
        ins_bg, ins_fg = styles.diff_insert_bg, styles.diff_insert_fg
        del_bg, del_fg = styles.diff_delete_bg, styles.diff_delete_fg
        for tv in ('output_textview', 'fmtstr_textview'):
            textview = getattr(self, tv)
            textview.create_tag('diff_insert', weight=700,
                                background_gdk=ins_bg, foreground_gdk=ins_fg)
            textview.create_tag('diff_delete', weight=700,
                                background_gdk=del_bg, foreground_gdk=del_fg)

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
            if isinstance(widget, PathEntry):
                widget.set_cwd(cwd)
        self.fields_vbox.foreach(_cb)

    def run(self, title, format_string, docstring=''):
        self.reset_fields()
        self.format_string = format_string
        self.diff_string = ''.join(f[0] for f in
                                   self.formatter.parse(format_string))
        self.fmtstr_textview.set_text(self.diff_string)
        self.title_lbl.set_text(title)
        field_names = self._parse_format_string(format_string)
        if not field_names:
            # no arguments, return command as is
            return gtk.RESPONSE_ACCEPT
        doc = self.set_docstring(docstring)
        self.set_fields(field_names, doc['parameters'])
        return self.widget.run()

    # ==================== State management ==================== #

    def toggle_direct_editing(self, direct_editing):
        for name, field in self.fields.items():
            field.set_sensitive(not direct_editing)
            field.set_editable(not direct_editing)
        self.output_textview.set_editable(direct_editing)
        if direct_editing:
            self.output_textview.handler_unblock(
                self.handlers['output_changed'])
        else:
            self.output_textview.handler_block(
                self.handlers['output_changed'])

    # ==================== Populating entry fields ==================== #

    def set_docstring(self, docstring=''):
        if not docstring:
            doc = {'text': '', 'parameters': {}}
        else:
            doc = doc_parser.parse(docstring)
            self.doc_lbl.set_markup(doc['text'])
        if not doc['text']:
            self.doc_lbl.hide()
        return doc

    def set_fields(self, field_names, parameters):
        for name in field_names:
            param_doc = parameters.get(name)
            self.add_field(name, param_doc)
        self.fields_vbox.show_all()
        self.update_preview()

    def reset_fields(self):
        for wname in ('title_lbl', 'doc_lbl', 'fmtstr_textview',
                      'output_textview'):
            getattr(self, wname).set_text('')
        self.fields = OrderedDict()
        for child in self.fields_vbox.get_children():
            self.fields_vbox.remove(child)

    def add_field(self, name, doc):
        field = Field.from_documentation(name, doc)
        field.connect('changed', self.on_field_change)
        self.fields_vbox.pack_start(field)
        self.fields[name] = field

    # ==================== Output handling ==================== #

    def get_output(self):
        args, kwargs = [], {}
        for name, field in self.fields.items():
            value = field.get_value()
            try:
                # we need to convert integer keys
                # because they won't work if used in kwargs...
                name = int(name)
                args.insert(name, value)
            except ValueError:
                kwargs[name] = value
        return self.format_string.format(*args, **kwargs)

    def update_preview(self):
        self.handlers['update_timeout'] = 0
        output = self.get_output()
        self.output_textview.set_text(output)
        self._update_diffs(output)

    def _parse_format_string(self, format_string):
        field_names = []
        for token in fmt_parser.parse(format_string):
            if token.type == T_PARAM:
                field_names.append(token.value['identifier'])
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

    def on_enter_state(self, state, new_state):
        if new_state == StrfmtDialogState.DIRECT_EDITING:
            self.toggle_direct_editing(True)

    def on_leave_state(self, state, old_state):
        if old_state == StrfmtDialogState.DIRECT_EDITING:
            self.toggle_direct_editing(False)

    def on_output_edit_cb_toggled(self, widget):
        editable = widget.get_active()
        if editable:
            self.state.enter(StrfmtDialogState.DIRECT_EDITING)
        else:
            self.state.leave(StrfmtDialogState.DIRECT_EDITING)

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