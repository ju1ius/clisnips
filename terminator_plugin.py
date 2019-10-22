#!/usr/bin/env python3
"""
clisnips_plugin.py - Terminator Plugin to add a snippet library
"""


import gi
gi.require_versions({
    'Gio': '2.0',
    'GLib': '2.0',
    'Gdk': '3.0',
    'Vte': '2.91',
})
from gi.repository import GLib, Gio, Gtk, GObject, Gdk, Vte

from terminatorlib.util import dbg
from terminatorlib import plugin
from terminatorlib.terminal import Terminal


AVAILABLE = ['CliSnipsMenu']


class CliSnipsClient:

    BUS_NAME = 'me.ju1ius.clisnips'
    OBJECT_PATH = '/me/ju1ius/clisnips'

    def __init__(self):
        self._bus: Gio.DBusConnection = None
        self._subscriptions = {}

    def connect(self):
        self._bus = Gio.bus_get_sync(Gio.BusType.SESSION)

    def disconnect(self):
        if self._bus and not self._bus.is_closed():
            for signal, subscription_id in self._subscriptions.items():
                self._bus.signal_unsubscribe(subscription_id)
            self._bus.close_sync()

    def activate(self):
        self._call('Activate', 'org.gtk.Application',  GLib.Variant('(a{sv})', [{}]))

    def set_cwd(self, cwd):
        self._call(
            'Activate',
            'org.gtk.Actions',
            GLib.Variant('(sava{sv})', ('set-cwd', [GLib.Variant('s', cwd)], {}))
        )

    def on_insert_snippet(self, callback):
        def cb(bus, sender, path, interface, signal, params, data=None):
            result = params.unpack()
            callback(*result)
        self._subscribe('insert_snippet', cb)

    def _on_insert_snippet(self, bus, sender, path, interface, signal, params, data=None):
        result = params.unpack()

    def _call(self, method, interface, parameters=None):
        self._bus.call(
            bus_name=self.BUS_NAME,
            object_path=self.OBJECT_PATH,
            interface_name=interface,
            method_name=method,
            parameters=parameters or GLib.Variant('()', tuple()),
            reply_type=None,
            flags=Gio.DBusCallFlags.NONE,
            timeout_msec=-1,
            cancellable=None,
            callback=None,
            user_data=None,
        )

    def _subscribe(self, signal, callback, data=None, interface=None, path=None):
        subscription_id = self._bus.signal_subscribe(
            sender=self.BUS_NAME,
            interface_name=interface or self.BUS_NAME,
            member=signal,
            object_path=path or self.OBJECT_PATH,
            arg0=None,
            flags=Gio.DBusSignalFlags.NONE,
            callback=callback,
            user_data=data,
        )
        self._subscriptions[signal] = subscription_id

    def _unsubscribe(self, signal):
        subscription_id = self._subscriptions[signal]
        self._bus.signal_unsubscribe(subscription_id)


class CliSnipsMenu(plugin.MenuItem):

    capabilities = ['terminal_menu']

    def __init__(self):
        super().__init__()
        self._terminal = None
        self._cwd = None
        self._handlers = {}
        self._client = CliSnipsClient()

    def unload(self):
        """
        Plugin API: called when plugin is unloaded
        """
        self._disconnect_signals()
        self._client.disconnect()
        self._terminal = None
        self._handlers = {}

    def callback(self, menu_items, menu, terminal):
        """
        Called on menu initialization
        """
        item = Gtk.MenuItem('CliSnips snippets library')
        item.connect('activate', self.on_activate, terminal)
        menu_items.append(item)

    def on_activate(self, widget, terminal):
        """
        Called when our menu item is activated
        """
        self._terminal = terminal
        self._client.connect()
        self._reconnect_signals()
        self._client.activate()
        self._set_cwd()
        self._client.on_insert_snippet(self._on_insert_snippet)

    def _reconnect_signals(self):
        self._disconnect_signals()
        self._connect_signals()

    def _connect_signals(self):
        self._handlers['focus'] = GObject.add_emission_hook(
            Terminal,
            'focus-in',
            self._on_terminal_focus_in
        )
        self._handlers["keypress"] = GObject.add_emission_hook(
            Vte.Terminal,
            'key-press-event',
            self._on_terminal_key_pressed
        )

    def _disconnect_signals(self):
        if self._handlers.get('focus'):
            GObject.remove_emission_hook(
                Terminal,
                'focus-in',
                self._handlers['focus']
            )
        if self._handlers.get('keypress'):
            GObject.remove_emission_hook(
                Vte.Terminal,
                'key-press-event',
                self._handlers['keypress']
            )

    def _set_cwd(self, cwd=None):
        if not cwd:
            cwd = self._terminal.get_cwd()
        if cwd == self._cwd:
            return
        self._cwd = cwd
        self._client.set_cwd(cwd)
        dbg(f'clisnips.set-cwd "{cwd}"')

    # ---------- Signals ---------- #

    def _on_insert_snippet(self, snippet: str):
        # We should use the following but it's broken...
        # see terminator/terminatorlib/terminal.py:1505
        # self._terminal.feed(snippet)
        self._terminal.vte.feed_child_binary(snippet.encode('utf-8'))

    def _on_terminal_focus_in(self, terminal):
        self._terminal = terminal
        self._set_cwd()
        return True

    def _on_terminal_key_pressed(self, vt, event):
        if event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            # Although we registered the emission hook on vte.Terminal,
            # the event is also fired by terminatorlib.window.Window ...
            if isinstance(vt, Vte.Terminal):
                dbg('CliSnipsMenu :: Enter pressed %s' % vt)
                self._on_keypress_enter()
        return True

    def _on_keypress_enter(self):
        handlers = {
            'change': None,
            'timeout': 0
        }
        vt = self._terminal.vte

        def _on_timeout():
            handlers['timeout'] = 0
            self._set_cwd()

        def _on_change(vt):
            vt.disconnect(handlers['change'])
            if handlers['timeout']:
                GObject.source_remove(handlers['timeout'])
            handlers['timeout'] = GLib.timeout_add(500, _on_timeout)

        handlers['change'] = vt.connect('contents-changed', _on_change)
