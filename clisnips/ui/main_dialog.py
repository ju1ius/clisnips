import os

import gobject
import glib
import gtk

from . import helpers
from .edit_dialog import EditDialog
from .strfmt_dialog import StringFormatterDialog
from ..db import SnippetsDatabase
from .. import config


__DIR__ = os.path.abspath(os.path.dirname(__file__))
UI_FILE = os.path.join(__DIR__, 'main_dialog.ui')

(
    COLUMN_ID,
    COLUMN_TITLE,
    COLUMN_CMD,
    COLUMN_DOC,
    COLUMN_TAGS
) = range(5)
COLUMNS = (int, str, str, str, str)


class MainDialog(helpers.BuildableWidgetDecorator, gobject.GObject):

    __gsignals__ = {
        'insert_command': (
            gobject.SIGNAL_RUN_LAST,
            gobject.TYPE_NONE,
            (gobject.TYPE_STRING,)
        ),
        'insert_command_dialog': (
            gobject.SIGNAL_RUN_LAST,
            gobject.TYPE_NONE,
            ()
        )
    }

    def __init__(self):
        gobject.GObject.__init__(self)
        helpers.BuildableWidgetDecorator.__init__(self, UI_FILE, 'main_dialog')
        #self.ui.set_translation_domain (config.PKG_NAME)
        self.widget.connect("destroy-event", self.on_destroy)
        self.widget.connect("delete-event", self.on_destroy)
        #self.widget.set_icon_name("gnome-main-menu")

        self.add_ui_widgets(
            'search_entry',
            'snip_list',
            'cancel_btn', 'apply_btn',
            'add_btn', 'edit_btn', 'delete_btn'
        )

        self.model = gtk.ListStore(*COLUMNS)
        for i in (COLUMN_TITLE, COLUMN_TAGS, COLUMN_CMD):
            col = gtk.TreeViewColumn()
            self.snip_list.append_column(col)
            cell = gtk.CellRendererText()
            if i == COLUMN_CMD:
                cell.set_property('font', config.font)
                col.set_property('expand', True)
            col.pack_start(cell, False)
            col.add_attribute(cell, 'text', i)

        self.db = SnippetsDatabase().open()
        self.load_snippets()

        self.search_results = set()

        self.edit_dialog = EditDialog()
        self.edit_dialog.set_transient_for(self.widget)
        self.string_formatter_dialog = StringFormatterDialog()
        self.string_formatter_dialog.set_transient_for(self.widget)

        self.connect_signals()

    def set_cwd(self, cwd):
        self.string_formatter_dialog.set_cwd(cwd)

    def emit(self, *args):
        """Ensures signals are emitted in the main thread"""
        glib.idle_add(gobject.GObject.emit, self, *args)

    def load_snippets(self):
        self.snip_list.set_model(None)
        self.model.clear()
        for row in self.db:
            self.model.append((
                row['rowid'],
                row['title'],
                row['cmd'],
                row['doc'],
                row['tag']
            ))
        self.snip_list.set_model(self.model)
        self.model_filter = self.model.filter_new()
        self.model_filter.set_visible_func(self.search_callback)

    def search_callback(self, mdl, it, data=None):
        rowid = mdl.get_value(it, COLUMN_ID)
        if rowid:
            return rowid in self.search_results

    def run(self):
        self.widget.show_all()

    def destroy(self):
        self.db.close()
        self.widget.destroy()

    def append_row(self, data):
        rowid = self.db.insert(data)
        self.db.save()
        self.model.append((
            rowid,
            data['title'],
            data['cmd'],
            data['doc'],
            data['tag'],
        ))

    def update_row(self, it, data):
        self.db.update(data)
        self.db.save()
        self.model.set(
            it,
            COLUMN_TITLE, data['title'],
            COLUMN_CMD, data['cmd'],
            COLUMN_DOC, data['doc'],
            COLUMN_TAGS, data['tag'],
        )

    def remove_row(self, it):
        self.db.delete(self.model.get_value(it, COLUMN_ID))
        self.model.remove(it)

    def insert_command(self, command, docstring):
        self.emit('insert-command-dialog')
        response = self.string_formatter_dialog.run(command, docstring)
        if response == gtk.RESPONSE_ACCEPT:
            output = self.string_formatter_dialog.get_output()
            self.emit('insert-command', output)

    def show_row_context_menu(self):
        menu = gtk.Menu()
        edit_item = gtk.ImageMenuItem(gtk.STOCK_EDIT)
        edit_item.connect('activate', self.on_edit_btn_clicked)
        menu.append(edit_item)
        delete_item = gtk.ImageMenuItem(gtk.STOCK_DELETE)
        delete_item.connect('activate', self.on_delete_btn_clicked)
        menu.append(delete_item)
        menu.append(gtk.SeparatorMenuItem())
        apply_item = gtk.ImageMenuItem(gtk.STOCK_APPLY)
        apply_item.connect('activate', self.on_apply_btn_clicked)
        menu.append(apply_item)
        menu.show_all()
        menu.popup(None, None, None, 3, 0)

    ###########################################################################
    # ------------------------------ SIGNALS
    ###########################################################################

    def on_destroy(self, dialog):
        self.destroy()

    def on_snip_list_button_release_event(self, treeview, event):
        if event.button == 3:  # right click
            self.show_row_context_menu()

    def on_snip_list_row_activated(self, treeview, path, col):
        mdl = treeview.get_model()
        it = mdl.get_iter(path)
        cmd, doc = mdl.get(it, COLUMN_CMD, COLUMN_DOC)
        self.insert_command(cmd, doc)

    def on_apply_btn_clicked(self, widget, data=None):
        selection = self.snip_list.get_selection()
        mdl, it = selection.get_selected()
        cmd, doc = mdl.get(it, COLUMN_CMD, COLUMN_DOC)
        self.insert_command(cmd, doc)

    def on_cancel_btn_clicked(self, widget, data=None):
        self.destroy()

    def on_add_btn_clicked(self, widget, data=None):
        response = self.edit_dialog.run()
        #print "response %s from result of run()" % response
        if response == gtk.RESPONSE_ACCEPT:
            data = self.edit_dialog.get_data()
            self.append_row(data)

    def on_edit_btn_clicked(self, widget, data=None):
        selection = self.snip_list.get_selection()
        if not selection:
            return
        mdl, it = selection.get_selected()
        values = mdl.get(it, COLUMN_ID, COLUMN_TITLE, COLUMN_CMD,
                         COLUMN_DOC, COLUMN_TAGS)
        data = {
            'id': values[0],
            'title': values[1],
            'cmd': values[2],
            'doc': values[3],
            'tag': values[4],
        }
        response = self.edit_dialog.run(data)
        if response == gtk.RESPONSE_ACCEPT:
            data = self.edit_dialog.get_data()
            if mdl is self.model_filter:
                it = mdl.convert_iter_to_child_iter(it)
            self.update_row(it, data)

    def on_delete_btn_clicked(self, widget, data=None):
        selection = self.snip_list.get_selection()
        mdl, it = selection.get_selected()
        if mdl is self.model_filter:
            it = mdl.convert_iter_to_child_iter(it)
        self.remove_row(it)

    def on_search_entry_changed(self, widget):
        query = widget.get_text()
        if not query:
            self.snip_list.set_model(self.model)
            return
        rows = self.db.search(query)
        if not rows:
            return
        self.search_results = set()
        for row in rows:
            self.search_results.add(row['docid'])
        self.model_filter.refilter()
        self.snip_list.set_model(self.model_filter)

    def on_search_entry_icon_press(self, widget, icon_pos, event):
        widget.set_text('')


gobject.type_register(MainDialog)
