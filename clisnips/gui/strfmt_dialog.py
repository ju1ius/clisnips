import os
import string
from collections import OrderedDict

import gtk
import glib

from ..config import styles
from .state import State
from .helpers import BuildableWidgetDecorator, SimpleTextView
from ..strfmt import doc_parser, fmt_parser
from ..strfmt.doc_tokens import T_PARAM
from ..diff import InlineMyersSequenceMatcher
from .strfmt_widgets import Field, PathEntry
from .error_dialog import ErrorDialog
from . import msg_dialogs 


__DIR__ = os.path.abspath(os.path.dirname(__file__))


class StrfmtDialogState(State):
    NORMAL_EDITING = 0x01
    DIRECT_EDITING = 0x02
    DIRECT_EDITING_DIRTY = 0x04


class StringFormatterDialog(BuildableWidgetDecorator):

    UI_FILE = os.path.join(__DIR__, 'resources', 'strfmt_dialog.ui')
    MAIN_WIDGET = 'main_dialog'
    WIDGET_IDS = ('title_lbl', 'doc_lbl', 'fields_vbox',
                  'fmtstr_lbl', 'fmtstr_textview',
                  'output_edit_cb', 'output_textview')
    UPDATE_TIMEOUT = 200

    def __init__(self):
        super(StringFormatterDialog, self).__init__()
        self.formatter = string.Formatter()
        # Parsed Documentation AST
        self._doc_tree = None
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
            if hasattr(widget, 'set_cwd'):
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
        self.set_docstring(docstring)
        self.set_fields(field_names)
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
            if StrfmtDialogState.DIRECT_EDITING_DIRTY in self.state:
                msg_dialogs.warning('Your edits will be lost if you modify '
                                    'one of the fields !')

    # ==================== Populating entry fields ==================== #

    def set_docstring(self, docstring=''):
        doc = doc_parser.parse(docstring)
        self.doc_lbl.set_markup(doc.header.strip())
        if not doc.header:
            self.doc_lbl.hide()
        self._doc_tree = doc

    def set_fields(self, field_names):
        parameters = self._doc_tree.parameters
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
        return self.output_textview.get_text()

    def update_preview(self):
        self.handlers['update_timeout'] = 0
        output = self.get_output()
        #
        args, kwargs = [], {}
        params = self._apply_code_blocks()
        for name, value in params.items():
            try:
                # we need to convert integer keys
                # because they won't work if used in kwargs...
                name = int(name)
                args.insert(name, value)
            except ValueError:
                kwargs[name] = value
        output = self.format_string.format(*args, **kwargs)
        #
        self.output_textview.set_text(output)
        self._update_diffs(output)

    def _parse_format_string(self, string):
        return [f['name'] for f in fmt_parser.parse(string)]

    def _apply_code_blocks(self):
        _vars = {'params': {}}
        for name, field in self.fields.items():
            _vars['params'][name] = field.get_value()
        for code in self._doc_tree.code_blocks:
            try:
                code.execute(_vars)
            except Exception as err:
                msg = 'Error while running code block: %s' % code
                ErrorDialog().run(err, msg)
        return _vars['params']

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
        self.state += StrfmtDialogState.DIRECT_EDITING_DIRTY
        self._update_diffs(widget.get_text())

    def on_reset_btn_clicked(self, widget):
        # reset output to format string
        self.output_textview.set_text(self.fmtstr_lbl.get_text())
        # then update with fields contents
        self.update_preview()

    def on_field_change(self, widget):
        self.state -= StrfmtDialogState.DIRECT_EDITING_DIRTY
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
