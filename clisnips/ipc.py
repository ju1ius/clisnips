from __future__ import print_function
import time

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

import gtk

DBusGMainLoop(set_as_default=True)

BUS_NAME = 'org.ju1ius.CliSnips'
BUS_PATH = '/org/ju1ius/CliSnips'


class CliSnipsService(dbus.service.Object):

    def __init__(self, window):
        self.window = window
        bus_name = dbus.service.BusName(BUS_NAME, bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, BUS_PATH)
        self._connect_signals()

    def _connect_signals(self):
        self.window.connect('insert-snippet', self._on_insert_snippet)

    @dbus.service.method(BUS_NAME)
    def activate(self):
        self.window.present_with_time(time.time())
        gtk.gdk.notify_startup_complete()

    @dbus.service.method(BUS_NAME, in_signature='s')
    def set_cwd(self, cwd):
        self.window.set_cwd(cwd)

    @dbus.service.signal(BUS_NAME, signature='s')
    def insert_snippet(self, snippet):
        return snippet

    def _on_insert_snippet(self, window, snippet):
        self.insert_snippet(snippet)


def with_proxy(func):
    """Decorator function to connect to the session bus"""

    def _exec(*args, **argd):
        print('dbus client call: %s' % func.func_name)
        bus = dbus.SessionBus()
        proxy = bus.get_object(BUS_NAME, BUS_PATH)
        func(proxy, *args, **argd)

    return _exec


@with_proxy
def set_cwd(session, cwd):
    session.set_cwd(cwd)
