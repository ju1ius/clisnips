#!/usr/bin/env python3
from __future__ import print_function
import sys
import time

import gtk
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop


#import clisnips.ipc
from clisnips.gui.main_dialog import MainDialog
from clisnips.gui.error_dialog import ErrorDialog


BUS_NAME = 'org.ju1ius.CliSnips'
BUS_PATH = '/org/ju1ius/CliSnips'


class Application(dbus.service.Object):

    def __init__(self, bus, path, name):
        dbus.service.Object.__init__(self, bus, path, name)
        self.running = False
        self.window = MainDialog()
        self._connect_signals()

    @dbus.service.method(BUS_NAME, in_signature='', out_signature='b')
    def IsRunning(self):
        return self.running

    @dbus.service.method(BUS_NAME, in_signature='a{sv}i', out_signature='')
    def Start(self, options, timestamp):
        if self.IsRunning():
            self.window.present_with_time(timestamp)
        else:
            self.running = True
            self._start()
            self.running = False

    @dbus.service.method(BUS_NAME, in_signature='', out_signature='')
    def Activate(self):
        self.window.present()
        gtk.gdk.notify_startup_complete()

    @dbus.service.method(BUS_NAME, in_signature='s', out_signature='s')
    def SetWorkingDirectory(self, cwd):
        self.window.set_cwd(cwd)
        return self.window.strfmt_dialog.cwd

    @dbus.service.signal(BUS_NAME, signature='s')
    def InsertSnippet(self, snippet):
        return snippet

    def _start(self):
        try:
            self.window.run()
            gtk.main()
        except Exception as err:
            ErrorDialog().run(err)
            sys.exit(127)

    def _connect_signals(self):
        self.window.connect('close', gtk.main_quit)
        self.window.connect('insert-snippet', self._on_insert_snippet)

    def _on_insert_snippet(self, window, snippet):
        self.InsertSnippet(snippet)


if __name__ == '__main__':

    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    request = bus.request_name(BUS_NAME, dbus.bus.NAME_FLAG_DO_NOT_QUEUE)
    if request != dbus.bus.REQUEST_NAME_REPLY_EXISTS:
        app = Application(bus, BUS_PATH, BUS_NAME)
    else:
        obj = bus.get_object(BUS_NAME, BUS_PATH)
        app = dbus.Interface(obj, BUS_NAME)

    # Get your options from the command line, e.g. with OptionParser
    options = {'option1': 'value1'}
    app.Start(options, int(time.time()))

    if app.IsRunning():
        gtk.gdk.notify_startup_complete()

    sys.exit(0)
