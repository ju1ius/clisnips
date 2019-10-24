import string
from collections import OrderedDict
from pathlib import Path

from gi.repository import GLib, Gtk

from . import msg_dialogs
from .buildable import Buildable
from .error_dialog import ErrorDialog
from .state import State
from .strfmt_widgets import Field
from .text_view import SimpleTextView
from ..config import styles
from ..diff import InlineMyersSequenceMatcher
from ..exceptions import ParsingError
from ..strfmt import doc_parser, fmt_parser

__DIR__ = Path(__file__).parent.absolute()


class StrfmtDialogState(State):
    NORMAL_EDITING = 1 << 0
    DIRECT_EDITING = 1 << 1
    DIRECT_EDITING_DIRTY = 1 << 2


@Buildable.from_file(__DIR__ / 'resources' / 'glade' / 'strfmt_dialog.glade')
class StringFormatterDialog:

    UPDATE_TIMEOUT = 200

    _dialog: Gtk.Dialog = Buildable.Child('strfmt_dialog')
    title_lbl: Gtk.Label = Buildable.Child()
    doc_lbl: Gtk.Label = Buildable.Child()
    fields_vbox: Gtk.Box = Buildable.Child()
    fmtstr_lbl: Gtk.Label = Buildable.Child()
    fmtstr_textview: Gtk.TextView = Buildable.Child()
    output_edit_cb: Gtk.CheckButton = Buildable.Child()
    output_textview: Gtk.TextView = Buildable.Child()

    def __init__(self, transient_for=None):
        super().__init__()
        self._dialog.set_transient_for(transient_for)

        self.formatter = string.Formatter()
        # Parsed Documentation AST
        self._doc_tree = None
        # the original format string
        self.format_string = ''
        # the string used for diffing and advanced editing
        self.diff_string = ''
        self.fields = OrderedDict()
        self.cwd = Path('~').expanduser()
        # state manager
        self.state = StrfmtDialogState()
        self.state.connect('enter-state', self.on_enter_state)
        self.state.connect('leave-state', self.on_leave_state)

        # output textview
        self.output_textview = SimpleTextView(self.output_textview)
        # format string textview
        self.fmtstr_textview = SimpleTextView(self.fmtstr_textview)
        self.fmtstr_textview.get_style_context().add_class('inverted')

        # diff tags
        ins_bg, ins_fg = styles.diff_insert_bg, styles.diff_insert_fg
        del_bg, del_fg = styles.diff_delete_bg, styles.diff_delete_fg
        for tv in ('output_textview', 'fmtstr_textview'):
            textview = getattr(self, tv)
            textview.create_tag('diff_insert', weight=700, background_rgba=ins_bg, foreground_rgba=ins_fg)
            textview.create_tag('diff_delete', weight=700, background_rgba=del_bg, foreground_rgba=del_fg)

        # signals
        self.handlers = {
            'update_timeout': 0,
            'output_changed': self.output_textview.connect('changed', self.on_output_changed)
        }
        self.output_textview.handler_block(self.handlers['output_changed'])
        # diff
        self.differ = InlineMyersSequenceMatcher()

    def set_cwd(self, cwd):
        self.cwd = cwd

        def _cb(widget):
            if hasattr(widget, 'set_cwd'):
                widget.set_cwd(cwd)
            elif hasattr(widget, 'foreach'):
                widget.foreach(_cb)

        self.fields_vbox.foreach(_cb)

    def run(self, title, format_string, docstring=''):
        try:
            field_names = self._parse_format_string(format_string)
        except ParsingError as err:
            ErrorDialog().run(err, 'You have an error in your snippet syntax:')
            return Gtk.ResponseType.REJECT

        if not field_names:
            # no arguments, return command as is
            self.output_textview.set_text(format_string)
            return Gtk.ResponseType.ACCEPT
        self.reset_fields()
        self.format_string = format_string
        self.diff_string = ''.join(f[0] for f in self.formatter.parse(format_string))
        self.fmtstr_textview.set_text(self.diff_string)
        self.title_lbl.set_text(title)

        try:
            self.set_docstring(docstring)
        except ParsingError as err:
            ErrorDialog().run(err, 'You have an error in your docstring syntax:')
            return Gtk.ResponseType.REJECT

        self.set_fields(field_names)
        # Ensure CWD is set on all fields
        self.set_cwd(self.cwd)
        return self._dialog.run()

    # ==================== State management ==================== #

    def toggle_direct_editing(self, direct_editing):
        for name, field in self.fields.items():
            field.set_sensitive(not direct_editing)
            field.set_editable(not direct_editing)
        self.output_textview.set_editable(direct_editing)
        if direct_editing:
            self.output_textview.handler_unblock(self.handlers['output_changed'])
        else:
            self.output_textview.handler_block(self.handlers['output_changed'])
            if StrfmtDialogState.DIRECT_EDITING_DIRTY in self.state:
                msg_dialogs.warning('Your edits will be lost if you modify one of the fields !')

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
        for wname in ('title_lbl', 'doc_lbl', 'fmtstr_textview', 'output_textview'):
            getattr(self, wname).set_text('')
        self.fields = OrderedDict()
        for child in self.fields_vbox.get_children():
            self.fields_vbox.remove(child)

    def add_field(self, name, doc):
        field = Field.from_documentation(name, doc)
        field.connect('changed', self.on_field_change)
        self.fields_vbox.pack_start(field, expand=True, fill=True, padding=0)
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
                ErrorDialog().run(err, f'Error while running code block:\n{code}')
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

    def on_field_change(self, widget):
        self.state -= StrfmtDialogState.DIRECT_EDITING_DIRTY
        if self.handlers['update_timeout']:
            GLib.source_remove(self.handlers['update_timeout'])
        self.handlers['update_timeout'] = GLib.timeout_add(self.UPDATE_TIMEOUT, self.update_preview)

    def on_output_changed(self, widget):
        self.state += StrfmtDialogState.DIRECT_EDITING_DIRTY
        self._update_diffs(widget.get_text())

    @Buildable.Callback()
    def on_output_edit_cb_toggled(self, widget):
        editable = widget.get_active()
        if editable:
            self.state.enter(StrfmtDialogState.DIRECT_EDITING)
        else:
            self.state.leave(StrfmtDialogState.DIRECT_EDITING)

    @Buildable.Callback()
    def on_reset_btn_clicked(self, widget):
        # reset output to format string
        self.output_textview.set_text(self.fmtstr_lbl.get_text())
        # then update with fields contents
        self.update_preview()

    @Buildable.Callback()
    def on_main_dialog_response(self, widget, response_id):
        if response_id == Gtk.ResponseType.ACCEPT:
            self._dialog.hide()
        elif response_id == Gtk.ResponseType.REJECT:
            self.reset_fields()
            self._dialog.hide()
        elif response_id == Gtk.ResponseType.DELETE_EVENT:
            self.reset_fields()
            self._dialog.hide()
            return True
        return False
