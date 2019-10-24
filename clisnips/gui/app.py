from pathlib import Path

import gi

gi.require_versions({
    'GLib': '2.0',
    'Gio': '2.0',
    'Gdk': '3.0',
    'Gtk': '3.0',
    'GtkSource': '3.0',
})
from gi.repository import Gtk, Gio, Gdk, GLib

from .app_window import AppWindow
from ..config import Config
from .about_dialog import AboutDialog

__DIR__ = Path(__file__).absolute().parent

APP_FLAGS = Gio.ApplicationFlags.HANDLES_COMMAND_LINE


class Application(Gtk.Application):

    def __init__(self):
        super().__init__(
            application_id='me.ju1ius.clisnips',
            flags=APP_FLAGS
        )
        self.window = None
        self._resource_path = __DIR__ / 'resources'
        self._css_provider = Gtk.CssProvider()
        self._config = Config()

        self.add_main_option(
            'database', 0,
            GLib.OptionFlags.NONE, GLib.OptionArg.STRING,
            'Path to a snippet database, or ":memory:" to use an in-memory database.', 'PATH'
        )

    def do_dbus_register(self, bus: Gio.DBusConnection, object_path: str):
        definition = self._resource_path / 'me.ju1ius.clisnips.xml'
        with open(definition, 'r') as fp:
            info: Gio.DBusNodeInfo = Gio.DBusNodeInfo.new_for_xml(fp.read())
            interface = info.lookup_interface('me.ju1ius.clisnips')
            bus.register_object(object_path, interface, None, None, None)
        return True

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self._add_action('quit', self.on_quit)
        self._add_action('open', self.on_import)
        self._add_action('new', self.on_import)
        self._add_action('import', self.on_import)
        self._add_action('export', self.on_export)
        self._add_action('about', self.on_about)
        self._add_action('set-cwd', self.on_set_cwd, GLib.VariantType('s'))
        self._load_menus()
        self._load_stylesheets()

    def do_command_line(self, cli: Gio.ApplicationCommandLine):
        options = cli.get_options_dict().end().unpack()
        if 'database' in options:
            # TODO: set database
            pass
        self.activate()
        return 0

    def do_activate(self):
        if not self.window:
            self.window = AppWindow(self, self._config)
            self.window.connect('insert-snippet', self.on_insert_snippet)
            self.window.run()
        self.window.present()

    def on_quit(self, action, param):
        self.window.destroy()
        self.quit()

    def on_import(self, action, param):
        pass

    def on_export(self, action, param):
        pass

    def on_about(self, actio, param):
        dlg = AboutDialog()
        dlg.run()
        dlg.destroy()

    def on_set_cwd(self, action, cwd: GLib.Variant):
        print(f'set-cwd: {cwd}')
        self.window.set_cwd(cwd.get_string())

    def on_insert_snippet(self, window, snippet):
        self.send_snippet(snippet)

    def send_snippet(self, snippet):
        bus: Gio.DBusConnection = self.get_dbus_connection()
        bus.emit_signal(
            None,  # broadcast to all listeners
            self.get_dbus_object_path(),
            'me.ju1ius.clisnips',
            'insert_snippet',
            GLib.Variant('(s)', (snippet,))
        )

    def _load_stylesheets(self):
        screen = Gdk.Screen.get_default()
        self._css_provider.load_from_path(str(self._resource_path / 'styles.css'))
        Gtk.StyleContext.add_provider_for_screen(screen, self._css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _load_menus(self):
        ui = Gtk.Builder()
        ui.add_from_file(str(self._resource_path / 'glade' / 'menus.glade'))
        self.set_app_menu(ui.get_object('app-menu'))

    def _add_action(self, name, callback, parameter_type=None):
        action = Gio.SimpleAction.new(name, parameter_type)
        action.connect('activate', callback)
        self.add_action(action)
