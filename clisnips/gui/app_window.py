from pathlib import Path

from gi.repository import GLib, GObject, Gdk, Gio, Gtk, Pango

from .action import add_action, add_stateful_action
from .buildable import Buildable
from .edit_dialog import EditDialog
from .error_dialog import ErrorDialog
from .import_export import ExportDialog, ImportDialog
from .open_dialog import CreateDialog, OpenDialog
from .state import State as BaseState
from .strfmt_dialog import StringFormatterDialog
from ..config import HELP_URI
from ..database.search_pager import SearchPager
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


@Buildable.from_file(__DIR__ / 'resources' / 'glade' / 'app-window.glade')
class AppWindow(GObject.GObject):

    window: Gtk.ApplicationWindow = Buildable.Child('app_window')

    search_entry: Gtk.SearchEntry = Buildable.Child()
    sort_options_menu_btn: Gtk.MenuButton = Buildable.Child()
    snip_list: Gtk.TreeView = Buildable.Child()

    pager_curpage_lbl: Gtk.Label = Buildable.Child()
    pager_info_lbl: Gtk.Label = Buildable.Child()

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

        # app actions
        app.lookup_action('open').connect('activate', self.on_open_action)
        app.lookup_action('new').connect('activate', self.on_app_new_action)
        app.lookup_action('import').connect('activate', self.on_import_action)
        app.lookup_action('export').connect('activate', self.on_export_action)
        # window actions
        add_action(self.window, 'snippet-apply', self.on_snippet_apply_action)
        add_action(self.window, 'snippet-add', self.on_snippet_add_action)
        add_action(self.window, 'snippet-edit', self.on_snippet_edit_action)
        add_action(self.window, 'snippet-delete', self.on_snippet_delete_action)
        add_stateful_action(self.window, 'order-by', self.on_order_by_action,
                            GLib.VariantType('s'), GLib.Variant('s', 'popularity'))
        for page in ('first', 'previous', 'next', 'last'):
            add_action(self.window, f'pager-{page}', self.on_pager_action)
        # Menus
        builder = Gtk.Builder()
        builder.add_from_file(str(__DIR__ / 'resources' / 'glade' / 'win-menu.glade'))
        menu = builder.get_object('sort-menu')
        self.sort_options_menu_btn.set_menu_model(menu)
        menu = builder.get_object('snippet-list-context-menu')
        self._context_menu: Gtk.Menu = Gtk.Menu.new_from_model(menu)
        self._context_menu.attach_to_widget(self.window)

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
        self.pager = SearchPager(self.db, page_size=self._config.pager_page_size)
        self.pager.set_sort_column(self._config.pager_sort_column)

    def load_snippets(self):
        """
        Loads the whole snippets database in the main treeview.

        Since loading is asynchronous, other methods MUST avoid
        operating on the model while state is in State.LOADING.
        """
        self.state += State.LOADING
        rows = self.pager.list()
        self._update_pager_view()
        self._load_rows(rows)
        self.state -= State.LOADING

    ###########################################################################
    # ------------------------------ ACTIONS
    ###########################################################################

    # ===== File Menu

    def on_open_action(self, action, param):
        filename = OpenDialog().run()
        if not filename:
            return
        try:
            self.set_database(filename)
            self.load_snippets()
        except Exception as err:
            self._error(err)

    def on_app_new_action(self, action, param):
        filename = CreateDialog().run()
        if not filename:
            return
        try:
            self.set_database(filename)
            self.load_snippets()
        except Exception as err:
            self._error(err)

    def on_import_action(self, action, param):
        try:
            ImportDialog().run(self.db)
        except Exception as err:
            self._error(err)
        else:
            self.load_snippets()

    def on_export_action(self, action, param):
        try:
            ExportDialog().run(self.db)
        except Exception as err:
            self._error(err)

    def on_helplink_menuitem_activate(self, menuitem):
        Gtk.show_uri(Gdk.Screen.get_default(), HELP_URI, int(GLib.get_current_time()))

    # ===== Display Menu

    def on_order_by_action(self, action, param: GLib.Variant):
        action.set_state(param)
        value = param.unpack()
        column = {
            'popularity': 'ranking',
            'creation-date': 'created_at',
            'usage-count': 'usage_count',
            'last-usage-date': 'last_used_at',
        }.get(value, 'ranking')
        self._change_sort_column(column)

    def _change_sort_column(self, column):
        self._config.pager_sort_column = column
        self._config.save()
        self.pager.set_sort_column(column)
        if self.pager.is_searching:
            rows = self.pager.search(self.get_search_text())
        else:
            rows = self.pager.list()
        self._load_rows(rows)

    # ===== SearchPager navigation

    def on_pager_action(self, action: Gio.SimpleAction, param=None):
        method = action.get_name().split('-')[-1]
        rows = getattr(self.pager, method)()
        self._update_pager_view()
        self._load_rows(rows)

    def _update_pager_view(self):
        page = self.pager.current_page
        self.pager_curpage_lbl.set_text(str(page))
        info = f'page {page} of {len(self.pager)} ({self.pager.total_rows} snippets)'
        self.pager_info_lbl.set_text(info)
        # Action states
        is_first, is_last = self.pager.is_first_page, self.pager.is_last_page
        self.window.lookup_action('pager-first').set_enabled(not is_first)
        self.window.lookup_action('pager-previous').set_enabled(not is_first)
        self.window.lookup_action('pager-next').set_enabled(not is_last)
        self.window.lookup_action('pager-last').set_enabled(not is_last)

    # ===== Snippets list actions

    def on_snippet_apply_action(self, action, param=None):
        try:
            row = self.get_selected_row()
            if row:
                self.insert_snippet(row)
        except Exception as error:
            self._error(error)

    def on_snippet_add_action(self, action, param=None):
        try:
            response = self.edit_dialog.run()
            if response == Gtk.ResponseType.ACCEPT:
                data = self.edit_dialog.get_data()
                self.insert_row(data)
        except Exception as error:
            self._error(error)

    def on_snippet_edit_action(self, action, param=None):
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

    def on_snippet_delete_action(self, action, param=None):
        try:
            model, it = self.get_selection()
            self.remove_row(it)
        except Exception as error:
            self._error(error)

    ###########################################################################
    # ------------------------------ SIGNALS
    ###########################################################################

    def emit(self, *args):
        """
        Ensures signals are emitted in the main thread
        """
        GLib.idle_add(GObject.GObject.emit, self, *args)

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
            self._context_menu.popup_at_pointer(event)

    @Buildable.Callback()
    def on_snip_list_row_activated(self, treeview, path, col):
        self.window.activate_action('snippet-apply')

    @Buildable.Callback()
    def on_snip_list_selection_changed(self, selection: Gtk.TreeSelection):
        model, it = selection.get_selected()
        for name in ('apply', 'edit', 'delete'):
            self.window.lookup_action(f'snippet-{name}').set_enabled(bool(it))

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
        query = self.get_search_text()
        if not query:
            self.load_snippets()
            return False
        rows = self.pager.search(query)
        self._update_pager_view()
        self._load_rows(rows)
        self.state -= State.SEARCHING
        return False

    ###########################################################################
    # ------------------------------ SUPPORT
    ###########################################################################

    def get_search_text(self):
        return self.search_entry.get_text().strip()

    def _error(self, err):
        ErrorDialog(transient_for=self.window).run(err)

    # ========== Methods for acting on data rows ========== #

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

    # ========== Methods for working with the treeview ========== #

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
