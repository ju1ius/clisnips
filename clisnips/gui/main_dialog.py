import os
import time

import gobject
import glib
import gtk

from .. import config 
from . import helpers
from .edit_dialog import EditDialog
from .strfmt_dialog import StringFormatterDialog
from .import_export import ImportDialog, ExportDialog
from .error_dialog import ErrorDialog
from .about_dialog import AboutDialog
from ..database.snippets_db import SnippetsDatabase
from .pager import Pager
from .state import State as BaseState


__DIR__ = os.path.abspath(os.path.dirname(__file__))


class State(BaseState):
    LOADING = 1 << 0
    SEARCHING = 1 << 1


class Model(gtk.ListStore):

    (
        COLUMN_ID,
        COLUMN_TITLE,
        COLUMN_CMD,
        COLUMN_TAGS,
        COLUMN_CREATED,
        COLUMN_LASTUSED,
        COLUMN_USAGE,
        COLUMN_RANKING
    ) = range(8)

    COLUMNS = (int, str, str, str, int, int, int, float)

    def __init__(self):
        super(Model, self).__init__(*self.COLUMNS)


class MainDialog(helpers.BuildableWidgetDecorator):

    # Constants needed for BuildableWidgetDecorator
    UI_FILE = os.path.join(__DIR__, 'resources', 'main_dialog.ui')
    MAIN_WIDGET = 'main_dialog'
    WIDGET_IDS = ('menubar', 'search_entry', 'snip_list',
                  'pager_first_btn', 'pager_prev_btn',
                  'pager_next_btn', 'pager_last_btn',
                  'pager_curpage_lbl',
                  'cancel_btn', 'apply_btn',
                  'add_btn', 'edit_btn', 'delete_btn')

    # Signals emited by this dialog
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

    # Delay before a search operation is fired.
    SEARCH_TIMEOUT = 300

    def __init__(self):
        super(MainDialog, self).__init__()
        self.state = State()
        #self.ui.set_translation_domain(config.PKG_NAME)
        self.widget.connect("destroy-event", self.on_destroy)
        self.widget.connect("delete-event", self.on_destroy)

        helpers.set_font(self.snip_list, config.styles.font)
        helpers.set_background_color(self.snip_list, config.styles.bgcolor)
        helpers.set_text_color(self.snip_list, config.styles.fgcolor)

        self.model = Model()
        for i in (Model.COLUMN_TITLE, Model.COLUMN_TAGS, Model.COLUMN_CMD):
            col = gtk.TreeViewColumn()
            cell = gtk.CellRendererText()
            #cell.set_property('font', styles.font)
            #cell.set_property('background', styles.bgcolor)
            #cell.set_property('foreground', styles.fgcolor)
            if i == Model.COLUMN_CMD:
                col.set_property('expand', True)
            elif i == Model.COLUMN_TITLE:
                cell.set_property('wrap-width', 300)
            col.pack_start(cell, False)
            col.add_attribute(cell, 'text', i)
            self.snip_list.append_column(col)

        self.db = SnippetsDatabase(config.database_path).open()
        self.pager = Pager(self.ui, self.db,
                           page_size=int(config.pager['page_size']))
        self.pager.set_sort_columns([
            (config.pager['sort_column'], 'DESC'),
            ('id', 'ASC', True)
        ])

        self._search_timeout = 0

        self.edit_dialog = EditDialog()
        self.edit_dialog.set_transient_for(self.widget)
        self.strfmt_dialog = StringFormatterDialog()
        self.strfmt_dialog.set_transient_for(self.widget)

        self.connect_signals()

    def run(self):
        """
        Main application entry point
        """
        self.state.reset()
        self.widget.show_all()
        self.load_snippets()

    def destroy(self):
        """
        Main application exit point
        """
        self.db.close()
        self.widget.destroy()

    def set_cwd(self, cwd):
        """
        Sets the current working directory for path completion widgets.
        """
        self.strfmt_dialog.set_cwd(cwd)

    def emit(self, *args):
        """
        Ensures signals are emitted in the main thread
        """
        glib.idle_add(gobject.GObject.emit, self, *args)

    def load_snippets(self):
        """
        Loads the whole snippets database in the main treeview.

        Since loading is asynchronous, other methods MUST avoid
        operating on the model while state is in State.LOADING.
        """
        self.state += State.LOADING
        self.pager.mode = Pager.MODE_LIST
        rows = self.pager.execute().first()
        self._load_rows(rows)
        self.state -= State.LOADING

    def _load_rows(self, rows):
        self.state += State.LOADING
        self.snip_list.set_model(None)
        self.model.clear()
        for row in rows:
            self.model.append((
                row['id'],
                row['title'],
                row['cmd'],
                row['tag'],
                row['created_at'],
                row['last_used_at'],
                row['usage_count'],
                row['ranking']
            ))
        self.snip_list.set_model(self.model)
        self.state -= State.LOADING

    # ========== Methods for acting on data rows ========== #

    def insert_row(self, data):
        rowid = self.db.insert(data)
        self.db.save()
        row = self.db.get(rowid)
        self.model.append((
            rowid,
            row['title'],
            row['cmd'],
            row['tag'],
            row['created_at'],
            row['last_used_at'],
            row['usage_count'],
            row['ranking']
        ))

    def update_row(self, it, data):
        self.db.update(data)
        self.db.save()
        row = self.db.get(data['id'])
        self.model.set(
            it,
            Model.COLUMN_TITLE, row['title'],
            Model.COLUMN_CMD, row['cmd'],
            Model.COLUMN_TAGS, row['tag'],
            Model.COLUMN_CREATED, row['created_at'],
            Model.COLUMN_LASTUSED, row['last_used_at'],
            Model.COLUMN_USAGE, row['usage_count'],
            Model.COLUMN_RANKING, row['ranking']
        )

    def remove_row(self, it):
        self.db.delete(self.model.get_value(it, Model.COLUMN_ID))
        self.model.remove(it)

    def insert_command(self, row):
        self.emit('insert-command-dialog')
        response = self.strfmt_dialog.run(row['title'], row['cmd'], row['doc'])
        if response == gtk.RESPONSE_ACCEPT:
            output = self.strfmt_dialog.get_output()
            self.db.use_snippet(row['id'])
            self.emit('insert-command', output)

    def get_search_text(self):
        return self.search_entry.get_text().strip()

    # ========== Methods for working with the treeview ========== #

    def _search_callback(self, model, it, data=None):
        rowid = model.get_value(it, Model.COLUMN_ID)
        if rowid is not None:
            return rowid in self._search_results

    def get_selection(self):
        selection = self.snip_list.get_selection()
        model, it = selection.get_selected()
        return model, it

    def get_selected_row(self):
        model, it = self.get_selection()
        if not model or not it:
            return
        rowid = model.get_value(it, Model.COLUMN_ID)
        row = self.db.get(rowid)
        return row

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

    # ===== Pager navigation

    def on_pager_first_btn_clicked(self, btn):
        rows = self.pager.first()
        self._load_rows(rows)

    def on_pager_prev_btn_clicked(self, btn):
        rows = self.pager.previous()
        self._load_rows(rows)

    def on_pager_next_btn_clicked(self, btn):
        rows = self.pager.next()
        self._load_rows(rows)

    def on_pager_last_btn_clicked(self, btn):
        rows = self.pager.last()
        self._load_rows(rows)

    # ===== Snippets list actions

    def on_destroy(self, dialog, event, data=None):
        self.destroy()

    def on_snip_list_button_release_event(self, treeview, event):
        """
        Handler for self.snip_list 'button-release-event' signal.

        Shows a row's contextmenu on right-click.
        """
        if event.button == 3:  # right click
            model, it = self.get_selection()
            if not model or not it:
                return
            self.show_row_context_menu()

    def on_snip_list_row_activated(self, treeview, path, col):
        """
        Handler for self.snip_list 'row-activated' signal.

        Inserts a command on row double-click.
        Opens the command dialog if needed.
        """
        model = treeview.get_model()
        it = model.get_iter(path)
        rowid = model.get_value(it, Model.COLUMN_ID)
        row = self.db.get(rowid)
        self.insert_command(row)

    def on_show_btn_clicked(self, widget, data=None):
        self.edit_dialog.set_editable(False)
        self.on_edit_btn_clicked(widget, data)
        self.edit_dialog.set_editable(True)

    def on_apply_btn_clicked(self, widget, data=None):
        """
        Handler for self.apply_btn 'clicked' and
        row context menu apply item 'activate' signals.

        See `self.on_snip_list_row_activated`.
        """
        try:
            row = self.get_selected_row()
            if row:
                self.insert_command(row)
        except Exception as error:
            ErrorDialog().run(error)

    def on_cancel_btn_clicked(self, widget, data=None):
        """
        Handler for self.cancel_btn 'clicked' signal.

        Closes this dialog without doing nothing.
        """
        self.destroy()

    def on_add_btn_clicked(self, widget, data=None):
        """
        Handler for self.add_btn 'clicked' signal.

        Opens an empty command editing dialog
        and inserts the new row into the treeview.
        """
        try:
            response = self.edit_dialog.run()
            if response == gtk.RESPONSE_ACCEPT:
                data = self.edit_dialog.get_data()
                self.insert_row(data)
        except Exception as error:
            ErrorDialog().run(error)

    def on_edit_btn_clicked(self, widget, data=None):
        """
        Handler for self.edit_btn 'clicked' and
        row context menu edit item 'activate' signals.

        Opens the edit dialog with the selected command.
        """
        model, it = self.get_selection()
        if not model or not it:
            return
        try:
            row = self.db.get(model.get_value(it, Model.COLUMN_ID))
            response = self.edit_dialog.run(row)
            if response == gtk.RESPONSE_ACCEPT:
                data = self.edit_dialog.get_data()
                self.update_row(it, data)
        except Exception as error:
            ErrorDialog().run(error)

    def on_delete_btn_clicked(self, widget, data=None):
        """
        Handler for self.delete_btn 'clicked' and
        row context menu delete item 'activate' signals.

        Deletes the selected row.
        """
        try:
            model, it = self.get_selection()
            self.remove_row(it)
        except Exception as error:
            ErrorDialog().run(error)

    # ===== Handle Search

    def on_search_entry_icon_press(self, widget, icon_pos, event):
        """
        Handler for self.search_entry 'icon-press' signal.

        Resets the search entry.
        """
        widget.set_text('')

    def on_search_entry_changed(self, widget):
        """
        Handler for self.search_entry 'changed' signal.

        Queues a request for a search operation. 
        """
        if self._search_timeout:
            glib.source_remove(self._search_timeout)
        self._search_timeout = glib.timeout_add(self.SEARCH_TIMEOUT,
                                                self._on_search_timeout)

    def _on_search_timeout(self):
        """
        The actual search method.
        """
        if State.LOADING in self.state:
            # Defer filtering if we are loading rows
            return True
        self.state += State.SEARCHING
        self._search_timeout = 0
        query = self.get_search_text()
        if not query:
            self.load_snippets()
            return False
        params = {'term': query}
        self.pager.mode = Pager.MODE_SEARCH
        rows = self.pager.execute(params, params).first()
        if not rows:
            return False
        self._load_rows(rows)
        self.state -= State.SEARCHING
        return False

    # ========== MenuBar items event handlers ========== #

    # ===== File Menu

    def on_import_menuitem_activate(self, menuitem):
        try:
            ImportDialog().run(self.db)
        except Exception as err:
            ErrorDialog().run(err)
        else:
            self.load_snippets()

    def on_export_menuitem_activate(self, menuitem):
        try:
            ExportDialog().run(self.db)
        except Exception as err:
            ErrorDialog().run(err)

    # ===== Display Menu

    def on_sort_ranking_menuitem_activate(self, menuitem):
        self._change_sort_columns([
            ('ranking', 'DESC'),
            ('id', 'ASC', True)
        ])

    def on_sort_created_menuitem_activate(self, menuitem):
        self._change_sort_columns([
            ('created_at', 'DESC'),
            ('id', 'ASC', True)
        ])

    def on_sort_last_used_menuitem_activate(self, menuitem):
        self._change_sort_columns([
            ('last_used_at', 'DESC'),
            ('id', 'ASC', True)
        ])

    def on_sort_usage_count_menuitem_activate(self, menuitem):
        self._change_sort_columns([
            ('usage_count', 'DESC'),
            ('id', 'ASC', True)
        ])

    def _change_sort_columns(self, columns):
        config.pager['sort_column'] = columns[0][0]
        self.pager.set_sort_columns(columns)
        if self.pager.mode == Pager.MODE_SEARCH:
            search = self.get_search_text()
            params = {'term': search} if search else ()
        else:
            params = ()
        rows = self.pager.execute(params, params).first()
        self._load_rows(rows)

    # ===== Help Menu

    def on_helplink_menuitem_activate(self, menuitem):
        gtk.show_uri(gtk.gdk.screen_get_default(),
                     config.HELP_URI,
                     int(glib.get_current_time()))

    def on_about_menuitem_activate(self, menuitem):
        dlg = AboutDialog()
        dlg.run()
        dlg.destroy()
