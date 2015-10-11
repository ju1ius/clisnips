"""
clisnips_plugin.py - Terminator Plugin to add a snippet library
"""

from os.path import join

import gtk
import gobject
import glib

import dbus
from dbus.mainloop.glib import DBusGMainLoop

from terminatorlib.util import get_config_dir, dbg
from terminatorlib import plugin
from terminatorlib.config import Config
from terminatorlib.terminal import Terminal
import vte

from clisnips.gui.main_dialog import MainDialog
from clisnips.gui.error_dialog import ErrorDialog
import clisnips.config


AVAILABLE = ['CliSnipsMenu']

BUS_NAME = 'org.ju1ius.CliSnips'
BUS_PATH = '/org/ju1ius/CliSnips'

DBusGMainLoop(set_as_default=True)


class CliSnipsMenu(plugin.MenuItem):

    capabilities = ['terminal_menu']

    def __init__(self):
        super(CliSnipsMenu, self).__init__()
        self.terminal = None
        self.cwd = None
        self.handlers = {}
        self.bus = None
        self.clisnips= None

    def unload(self):
        self.disconnect_signals()
        self.terminal = None
        self.handlers = {}
        self.clisnips = None
        self.bus = None

    def callback(self, menuitems, menu, terminal):
        menuitem = gtk.MenuItem('CliSnips snippets library')
        menuitem.connect('activate', self.on_activate, terminal)
        menuitems.append(menuitem)

    def on_activate(self, widget, terminal):
        self.terminal = terminal
        self.reconnect_signals()
        #self.open_dialog()
        self.set_cwd()
        #self.set_styles()
        #self.save_config()

    def reconnect_signals(self):
        self.disconnect_signals()
        self.connect_signals()

    def connect_signals(self):
        # Install DBus handlers
        dbg('CliSnipsMenu :: Connecting to Session Bus')
        self.bus = dbus.SessionBus()
        clisnips_service = self.bus.get_object(BUS_NAME, BUS_PATH)
        self.clisnips = dbus.Interface(clisnips_service, BUS_NAME)
        self.bus.add_signal_receiver(self.on_insert_snippet,
                                     dbus_interface=BUS_NAME,
                                     signal_name='InsertSnippet')

        # Connect terminal focus signal
        self.handlers['focus'] = gobject.add_emission_hook(
            Terminal,
            'focus-in',
            self.on_terminal_focus_in
        )
        self.handlers["keypress"] = gobject.add_emission_hook(
            vte.Terminal,
            'key-press-event',
            self.on_terminal_key_pressed
        )

    def disconnect_signals(self):
        if self.bus:
            self.bus.close()
        if self.handlers.get('focus'):
            gobject.remove_emission_hook(
                Terminal,
                'focus-in',
                self.handlers['focus']
            )
        if self.handlers.get('keypress'):
            gobject.remove_emission_hook(
                vte.Terminal,
                'key-press-event',
                self.handlers['keypress']
            )

    def open_dialog(self):
        def _success():
            pass
        def _error(e):
            raise e
        self.clisnips.Activate()

    def set_cwd(self, cwd=None):
        if cwd is None:
            cwd = self.terminal.get_cwd()
        if cwd == self.cwd:
            return
        self.cwd = cwd
        cwd = self.clisnips.SetWorkingDirectory(cwd)
        dbg('clisnips.SetWorkingDirectory "%s"' % cwd)

    # ---------- Signals ---------- #

    def on_terminal_focus_in(self, terminal):
        self.terminal = terminal
        self.set_cwd()
        return True

    def on_insert_snippet(self, snippet):
        self.terminal.feed(str(snippet).strip())

    def on_terminal_key_pressed(self, vt, event):
        kv = event.keyval
        if kv in (gtk.keysyms.Return, gtk.keysyms.KP_Enter):
            # Although we registered the emission hook on vte.Terminal,
            # the event is also fired by terminatorlib.window.Window ...
            if isinstance(vt, vte.Terminal):
                dbg('CliSnipsMenu :: Enter pressed %s' % vt)
                self.on_keypress_enter()
        return True

    def on_keypress_enter(self):
        handlers = {
            'change': None,
            'timeout': 0
        }
        vt = self.terminal.vte

        def _on_timeout():
            handlers['timeout'] = 0
            self.set_cwd()

        def _on_change(vt):
            vt.disconnect(handlers['change'])
            if handlers['timeout']:
                glib.source_remove(handlers['timeout'])
            handlers['timeout'] = glib.timeout_add(500, _on_timeout)

        handlers['change'] = vt.connect('contents-changed', _on_change)

    # ---------- Deprecated ---------- #

    #def configure(self):
        #plugin = self.__class__.__name__
        #config = self.config.plugin_get_config(plugin)
        #if not config:
            #self.config.plugin_set(plugin, 'pager', clisnips.config.pager)
            #self.config.plugin_set(plugin, 'database_path',
                                   #join(self.config_dir, 'plugins',
                                        #'clisnips.sqlite'))
        #clisnips.config.pager = self.config.plugin_get(plugin, 'pager')
        #clisnips.config.database_path = self.config.plugin_get(plugin,
                                                               #'database_path')

    #def set_styles(self):
        #try:
            #if self.config['use_system_font']:
                #font = self.config.get_system_font()
            #else:
                #font = self.config['font']
        #except:
            #pass
        #styles = clisnips.config.styles
        #styles.font = font
        #styles.bgcolor = self.terminal.bgcolor
        #styles.fgcolor = self.terminal.fgcolor_active
        #styles.cursor_color = self.config['cursor_color']

    #def save_config(self):
        #plugin = self.__class__.__name__
        #self.config.plugin_set_config(plugin, {
            #'pager': {
                #'sort_column': clisnips.config.pager['sort_column'],
                #'page_size': clisnips.config.pager['page_size']
            #},
            #'database_path': clisnips.config.database_path
        #})
        #self.config.save()
