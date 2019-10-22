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

from clisnips.gui.app_window import MainDialog


__DIR__ = Path(__file__).absolute().parent


class Application(Gtk.Application):

    def __init__(self):
        super().__init__(
            application_id='me.ju1ius.clisnips',
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        self.window = None
        self._resource_path = __DIR__ / 'resources'
        self._css_provider = Gtk.CssProvider()

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self._add_action('quit', self.on_quit)
        self._add_action('set-cwd', self.on_set_cwd, GLib.VariantType('s'))
        self._register_dbus_interface()
        self._load_stylesheets()

    def do_activate(self):
        Gtk.Application.do_activate(self)
        if not self.window:
            self.window = MainDialog(self)
            self.window.connect('insert-snippet', self.on_insert_snippet)
            self.window.run()
        self.window.present()

    def on_quit(self, action, param):
        self.window.destroy()
        self.quit()

    def on_set_cwd(self, action, cwd: GLib.Variant):
        print(f'set-cwd: {cwd}')
        self.window.set_cwd(cwd.get_string())

    def on_insert_snippet(self, window, snippet):
        self.send_snippet(snippet)

    def send_snippet(self, snippet):
        bus: Gio.DBusConnection = self.get_dbus_connection()
        bus.emit_signal(
            None,
            # 'me.ju1ius.clisnips',
            self.get_dbus_object_path(),
            'me.ju1ius.clisnips',
            'insert_snippet',
            GLib.Variant('(s)', (snippet,))
        )

    def _register_dbus_interface(self):
        bus: Gio.DBusConnection = self.get_dbus_connection()
        definition = self._resource_path / 'me.ju1ius.clisnips.xml'
        with open(definition, 'r') as fp:
            info: Gio.DBusNodeInfo = Gio.DBusNodeInfo.new_for_xml(fp.read())
            bus.register_object(
                self.get_dbus_object_path(),
                info.lookup_interface('me.ju1ius.clisnips'),
                None,
                None,
                None
            )

    def _load_stylesheets(self):
        self._css_provider.load_from_path(str(self._resource_path / 'styles.css'))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            self._css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _add_action(self, name, callback, parameter_type=None):
        action = Gio.SimpleAction.new(name, parameter_type)
        action.connect('activate', callback)
        self.add_action(action)
