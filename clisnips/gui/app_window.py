from pathlib import Path

from gi.repository import GLib, GObject, Gdk, Gtk, Pango

from .about_dialog import AboutDialog
from .buildable import Buildable
from .edit_dialog import EditDialog
from .error_dialog import ErrorDialog
from .import_export import ExportDialog, ImportDialog
from .open_dialog import CreateDialog, OpenDialog
from .pager import Pager
from .state import State as BaseState
from .strfmt_dialog import StringFormatterDialog
from ..config import HELP_URI
from ..database.snippets_db import SnippetsDatabase

__DIR__ = Path(__file__).parent.absolute()


class State(BaseState):
    LOADING = 1 << 0
    SEARCHING = 1 << 1


class Model(Gtk.ListStore):

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
        super().__init__(*self.COLUMNS)


@Buildable.from_file(__DIR__ / 'resources' / 'glade' / 'test.glade')
class AppWindow(GObject.GObject):

    window: Gtk.ApplicationWindow = Buildable.Child('app_window')
    search_entry: Gtk.SearchEntry = Buildable.Child()
    snip_list: Gtk.TreeView = Buildable.Child()
    pager_first_btn: Gtk.Button = Buildable.Child()
    pager_prev_btn: Gtk.Button = Buildable.Child()
    pager_next_btn: Gtk.Button = Buildable.Child()
    pager_last_btn: Gtk.Button = Buildable.Child()
    pager_curpage_lbl: Gtk.Label = Buildable.Child()
    add_btn: Gtk.Button = Buildable.Child()
    edit_btn: Gtk.Button = Buildable.Child()
    delete_btn: Gtk.Button = Buildable.Child()
    apply_btn: Gtk.Button = Buildable.Child()

    # Signals emited by this dialog
    __gsignals__ = {
        'insert-snippet': (
            GObject.SignalFlags.RUN_LAST,
            None,
            (GObject.TYPE_STRING,)
        ),
        'insert-snippet-dialog': (
            GObject.SignalFlags.RUN_LAST,
            None,
            ()
        ),
        'close': (
            GObject.SignalFlags.RUN_LAST,
            None,
            ()
        )
    }

    def __init__(self, app: Gtk.Application, config):
        GObject.GObject.__init__(self)
        self.window.set_application(application=app)

        app.lookup_action('open').connect('activate', self.on_open_action_activate)
        app.lookup_action('new').connect('activate', self.on_new_action_activate)
        app.lookup_action('import').connect('activate', self.on_import_action_activate)
        app.lookup_action('export').connect('activate', self.on_export_action_activate)

        self._config = config
        self.state = State()
        self.model = Model()

        for i in (Model.COLUMN_CMD, Model.COLUMN_TITLE, Model.COLUMN_TAGS):
            col = Gtk.TreeViewColumn()
            cell = Gtk.CellRendererText()
            if i == Model.COLUMN_CMD:
                cell.set_property('wrap-mode', Pango.WrapMode.WORD)
            elif i == Model.COLUMN_TITLE:
                cell.set_property('wrap-mode', Pango.WrapMode.WORD_CHAR)
            col.pack_start(cell, expand=False)
            col.add_attribute(cell, 'text', i)
            self.snip_list.append_column(col)

        self.db = None
        self.pager = None
        self.set_database(self._config.database_path)

        self._search_timeout = 0

        self.edit_dialog = EditDialog(transient_for=self.window)
        self.strfmt_dialog = StringFormatterDialog(transient_for=self.window)

    def run(self):
        """
        Main application entry point
        """
        self.state.reset()
        self.window.show_all()
        self.load_snippets()

    def destroy(self):
        """
        Main application exit point
        """
        self.db.close()
        self.window.destroy()
        self.emit('close')

    def present(self):
        self.window.present()

    def set_cwd(self, cwd):
        """
        Sets the current working directory for path completion widgets.
        """
        self.strfmt_dialog.set_cwd(cwd)

    def set_database(self, db_file):
        old_db = self.db
        try:
            self.db = SnippetsDatabase.open(db_file)
        except:
            raise
        if old_db:
            old_db.close()
        if db_file != ':memory:':
            self._config.database_path = db_file
            self._config.save()
        self.pager = Pager(self._gtk_builder, self.db, page_size=self._config.pager_page_size)
        self.pager.set_sort_columns([
            (self._config.pager_sort_column, 'DESC'),
            ('id', 'ASC', True)
        ])

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

    def insert_snippet(self, row):
        self.emit('insert-snippet-dialog')
        try:
            response = self.strfmt_dialog.run(row['title'], row['cmd'], row['doc'])
        except Exception as err:
            self._error(err)
        else:
            if response == Gtk.ResponseType.ACCEPT:
                output = self.strfmt_dialog.get_output()
                self.db.use_snippet(row['id'])
                self.emit('insert-snippet', output)

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
        menu = Gtk.Menu()
        for sid, cb in (('_Apply', self.on_apply_btn_clicked),
                        ('_Properties', self.on_show_btn_clicked)):
            self._add_context_menu_item(menu, sid, cb)
        menu.append(Gtk.SeparatorMenuItem())
        for sid, cb in ((Gtk.STOCK_EDIT, self.on_edit_btn_clicked),
                        ('_Delete', self.on_delete_btn_clicked)):
            self._add_context_menu_item(menu, sid, cb)
        menu.show_all()
        menu.popup(None, None, None, None, 3, 0)

    def _add_context_menu_item(self, menu, stock_id, cb):
        item = Gtk.MenuItem.new_with_mnemonic(stock_id)
        item.connect('activate', cb)
        menu.append(item)

    def _error(self, err):
        ErrorDialog(transient_for=self.window).run(err)

    ###########################################################################
    # ------------------------------ SIGNALS
    ###########################################################################

    def emit(self, *args):
        """
        Ensures signals are emitted in the main thread
        """
        GLib.idle_add(GObject.GObject.emit, self, *args)

    # ===== Pager navigation

    @Buildable.Callback()
    def on_pager_first_btn_clicked(self, btn):
        rows = self.pager.first()
        self._load_rows(rows)

    @Buildable.Callback()
    def on_pager_prev_btn_clicked(self, btn):
        rows = self.pager.previous()
        self._load_rows(rows)

    @Buildable.Callback()
    def on_pager_next_btn_clicked(self, btn):
        rows = self.pager.next()
        self._load_rows(rows)

    @Buildable.Callback()
    def on_pager_last_btn_clicked(self, btn):
        rows = self.pager.last()
        self._load_rows(rows)

    # ===== Snippets list actions

    def on_destroy(self, dialog, event, data=None):
        self.destroy()

    @Buildable.Callback()
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

    @Buildable.Callback()
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
        self.insert_snippet(row)

    @Buildable.Callback()
    def on_show_btn_clicked(self, widget, data=None):
        self.edit_dialog.set_editable(False)
        self.on_edit_btn_clicked(widget, data)
        self.edit_dialog.set_editable(True)

    @Buildable.Callback()
    def on_apply_btn_clicked(self, widget, data=None):
        """
        Handler for self.apply_btn 'clicked' and
        row context menu apply item 'activate' signals.

        See `self.on_snip_list_row_activated`.
        """
        try:
            row = self.get_selected_row()
            if row:
                self.insert_snippet(row)
        except Exception as error:
            self._error(error)

    @Buildable.Callback()
    def on_cancel_btn_clicked(self, widget, data=None):
        """
        Handler for self.cancel_btn 'clicked' signal.

        Closes this dialog without doing nothing.
        """
        self.destroy()

    @Buildable.Callback()
    def on_add_btn_clicked(self, widget, data=None):
        """
        Handler for self.add_btn 'clicked' signal.

        Opens an empty command editing dialog
        and inserts the new row into the treeview.
        """
        try:
            response = self.edit_dialog.run()
            if response == Gtk.ResponseType.ACCEPT:
                data = self.edit_dialog.get_data()
                self.insert_row(data)
        except Exception as error:
            self._error(error)

    @Buildable.Callback()
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
            if response == Gtk.ResponseType.ACCEPT:
                data = self.edit_dialog.get_data()
                self.update_row(it, data)
        except Exception as error:
            self._error(error)

    @Buildable.Callback()
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
            self._error(error)

    # ===== Handle Search

    @Buildable.Callback()
    def on_search_changed(self, widget):
        """
        Handler for self.search_entry 'search-changed' signal.
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

    def on_open_action_activate(self, action, param):
        filename = OpenDialog().run()
        if not filename:
            return
        try:
            self.set_database(filename)
            self.load_snippets()
        except Exception as err:
            self._error(err)

    def on_new_action_activate(self, action, param):
        filename = CreateDialog().run()
        if not filename:
            return
        try:
            self.set_database(filename)
            self.load_snippets()
        except Exception as err:
            self._error(err)

    def on_import_action_activate(self, action, param):
        try:
            ImportDialog().run(self.db)
        except Exception as err:
            self._error(err)
        else:
            self.load_snippets()

    def on_export_action_activate(self, action, param):
        try:
            ExportDialog().run(self.db)
        except Exception as err:
            self._error(err)

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
        self._config.pager_sort_column = columns[0][0]
        self._config.save()
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
        Gtk.show_uri(Gdk.Screen.get_default(), HELP_URI, int(GLib.get_current_time()))

    def on_about_menuitem_activate(self, menuitem):
        dlg = AboutDialog()
        dlg.run()
        dlg.destroy()
