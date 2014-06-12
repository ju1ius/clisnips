import os

import gobject
import glib
import gtk

from ..config import styles
from . import helpers
from .edit_dialog import EditDialog
from .strfmt_dialog import StringFormatterDialog
from ..db import SnippetsDatabase


__DIR__ = os.path.abspath(os.path.dirname(__file__))

(
    COLUMN_ID,
    COLUMN_TITLE,
    COLUMN_CMD,
    COLUMN_TAGS
) = range(4)
COLUMNS = (int, str, str, str)


class MainDialog(helpers.BuildableWidgetDecorator):

    SEARCH_TIMEOUT = 300

    UI_FILE = os.path.join(__DIR__, 'main_dialog.ui')
    MAIN_WIDGET = 'main_dialog'
    WIDGET_IDS = ('search_entry', 'snip_list',
                  'cancel_btn', 'apply_btn',
                  'add_btn', 'edit_btn', 'delete_btn')

    __gsignals__ = {
        'insert-command': (
            gobject.SIGNAL_RUN_LAST,
            gobject.TYPE_NONE,
            (gobject.TYPE_STRING,)
        ),
        'insert-command-dialog': (
            gobject.SIGNAL_RUN_LAST,
            gobject.TYPE_NONE,
            ()
        )
    }

    def __init__(self):
        super(MainDialog, self).__init__()
        #self.ui.set_translation_domain(config.PKG_NAME)
        self.widget.connect("destroy-event", self.on_destroy)
        self.widget.connect("delete-event", self.on_destroy)

        helpers.set_font(self.snip_list, styles.font)
        helpers.set_background_color(self.snip_list, styles.bgcolor)
        helpers.set_text_color(self.snip_list, styles.fgcolor)

        self.model = gtk.ListStore(*COLUMNS)
        for i in (COLUMN_TITLE, COLUMN_TAGS, COLUMN_CMD):
            col = gtk.TreeViewColumn()
            self.snip_list.append_column(col)
            cell = gtk.CellRendererText()
            #cell.set_property('font', styles.font)
            #cell.set_property('background', styles.bgcolor)
            #cell.set_property('foreground', styles.fgcolor)
            if i == COLUMN_CMD:
                col.set_property('expand', True)
            elif i == COLUMN_TITLE:
                cell.set_property('wrap-width', 300)
            col.pack_start(cell, False)
            col.add_attribute(cell, 'text', i)

        self.db = SnippetsDatabase().open()

        self._search_results = set()
        self._search_timeout = 0

        self.edit_dialog = EditDialog()
        self.edit_dialog.set_transient_for(self.widget)
        self.strfmt_dialog = StringFormatterDialog()
        self.strfmt_dialog.set_transient_for(self.widget)

        self.connect_signals()

    def set_cwd(self, cwd):
        self.strfmt_dialog.set_cwd(cwd)

    def emit(self, *args):
        """Ensures signals are emitted in the main thread"""
        glib.idle_add(gobject.GObject.emit, self, *args)

    def load_snippets(self):
        # load snippets in idle callback to avoid UI blocking
        glib.idle_add(self._do_load_snippets)

    def _do_load_snippets(self):
        self.snip_list.set_model(None)
        self.model.clear()
        for row in self.db.iter('rowid', 'title', 'cmd', 'tag'):
            self.model.append((
                row['rowid'],
                row['title'],
                row['cmd'],
                row['tag']
            ))
        self.snip_list.set_model(self.model)
        self.model_filter = self.model.filter_new()
        self.model_filter.set_visible_func(self._search_callback)
        return False

    def _search_callback(self, model, it, data=None):
        rowid = model.get_value(it, COLUMN_ID)
        if rowid is not None:
            return rowid in self._search_results

    def run(self):
        self.widget.show_all()
        self.load_snippets()

    def destroy(self):
        self.db.close()
        self.widget.destroy()

    def get_selection(self):
        selection = self.snip_list.get_selection()
        model, it = selection.get_selected()
        if model is self.model_filter:
            it = model.convert_iter_to_child_iter(it)
        return self.model, it

    def get_selected_row(self):
        model, it = self.get_selection()
        if not model or not it:
            return
        rowid = model.get_value(it, COLUMN_ID)
        row = self.db.get(rowid)
        return row

    def append_row(self, data):
        rowid = self.db.insert(data)
        self.db.save()
        self.model.append((
            rowid,
            data['title'],
            data['cmd'],
            data['tag'],
        ))

    def update_row(self, it, data):
        self.db.update(data)
        self.db.save()
        self.model.set(
            it,
            COLUMN_TITLE, data['title'],
            COLUMN_CMD, data['cmd'],
            COLUMN_TAGS, data['tag'],
        )

    def remove_row(self, it):
        self.db.delete(self.model.get_value(it, COLUMN_ID))
        self.model.remove(it)

    def insert_command(self, title, command, docstring):
        self.emit('insert-command-dialog')
        response = self.strfmt_dialog.run(title, command, docstring)
        if response == gtk.RESPONSE_ACCEPT:
            output = self.strfmt_dialog.get_output()
            self.emit('insert-command', output)

    def show_row_context_menu(self):
        menu = gtk.Menu()
        for sid, cb in ((gtk.STOCK_APPLY, self.on_apply_btn_clicked),
                        (gtk.STOCK_PROPERTIES, self.on_show_btn_clicked)):
            self._add_context_menu_item(menu, sid, cb)
        menu.append(gtk.SeparatorMenuItem())
        for sid, cb in ((gtk.STOCK_EDIT, self.on_edit_btn_clicked),
                        (gtk.STOCK_DELETE, self.on_delete_btn_clicked)):
            self._add_context_menu_item(menu, sid, cb)
        menu.show_all()
        menu.popup(None, None, None, 3, 0)

    def _add_context_menu_item(self, menu, stock_id, cb):
        item = gtk.ImageMenuItem(stock_id)
        item.connect('activate', cb)
        menu.append(item)

    ###########################################################################
    # ------------------------------ SIGNALS
    ###########################################################################

    def on_destroy(self, dialog, event, data=None):
        self.destroy()

    def on_snip_list_button_release_event(self, treeview, event):
        """
        Handler for self.snip_list 'button-release-event' signal
        """
        if event.button == 3:  # right click
            model, it = self.get_selection()
            if not model or not it:
                return
            self.show_row_context_menu()

    def on_snip_list_row_activated(self, treeview, path, col):
        """
        Handler for self.snip_list 'row-activated' signal
        """
        model = treeview.get_model()
        it = model.get_iter(path)
        rowid = model.get_value(it, COLUMN_ID)
        row = self.db.get(rowid)
        self.insert_command(row['title'], row['cmd'], row['doc'])

    def on_show_btn_clicked(self, widget, data=None):
        self.edit_dialog.set_editable(False)
        self.on_edit_btn_clicked(widget, data)
        self.edit_dialog.set_editable(True)

    def on_apply_btn_clicked(self, widget, data=None):
        """
        Handler for self.apply_btn 'clicked' and
        row context menu apply item 'activate' signals
        """
        row = self.get_selected_row()
        if row:
            self.insert_command(row['title'], row['cmd'], row['doc'])

    def on_cancel_btn_clicked(self, widget, data=None):
        """
        Handler for self.cancel_btn 'clicked' signal
        """
        self.destroy()

    def on_add_btn_clicked(self, widget, data=None):
        """
        Handler for self.add_btn 'clicked' signal
        """
        response = self.edit_dialog.run()
        if response == gtk.RESPONSE_ACCEPT:
            data = self.edit_dialog.get_data()
            self.append_row(data)

    def on_edit_btn_clicked(self, widget, data=None):
        """
        Handler for self.edit_btn 'clicked' and
        row context menu edit item 'activate' signals
        """
        model, it = self.get_selection()
        if not model or not it:
            return
        row = self.db.get(model.get_value(it, COLUMN_ID))
        response = self.edit_dialog.run(row)
        if response == gtk.RESPONSE_ACCEPT:
            data = self.edit_dialog.get_data()
            self.update_row(it, data)

    def on_delete_btn_clicked(self, widget, data=None):
        """
        Handler for self.delete_btn 'clicked' and
        row context menu delete item 'activate' signals
        """
        model, it = self.get_selection()
        self.remove_row(it)

    def on_search_entry_icon_press(self, widget, icon_pos, event):
        """
        Handler for self.search_entry 'icon-press' signal
        """
        widget.set_text('')

    def on_search_entry_changed(self, widget):
        """
        Handler for self.search_entry 'changed' signal
        """
        if self._search_timeout:
            glib.source_remove(self._search_timeout)
        self._search_timeout = glib.timeout_add(self.SEARCH_TIMEOUT,
                                                self._on_search_timeout)

    def _on_search_timeout(self):
        self._search_timeout = 0
        query = self.search_entry.get_text().strip()
        if not query:
            self.snip_list.set_model(self.model)
            self._search_results = set()
            return
        rows = self.db.search(query)
        if not rows:
            self._search_results = set()
            return
        self._search_results = set(row['docid'] for row in rows)
        self.snip_list.set_model(None)
        self.model_filter.refilter()
        self.snip_list.set_model(self.model_filter)

        return False
