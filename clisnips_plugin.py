"""
clisnips_plugin.py - Terminator Plugin to add a snippet library
"""

import gtk
import gobject

from terminatorlib import plugin
from terminatorlib.config import Config
from terminatorlib.terminal import Terminal

from clisnips.gui.main_dialog import MainDialog
from clisnips.gui.error_dialog import ErrorDialog
import clisnips.config


AVAILABLE = ['CliSnipsMenu']


class CliSnipsMenu(plugin.MenuItem):

    capabilities = ['terminal_menu']

    def __init__(self):
        super(CliSnipsMenu, self).__init__()
        self.terminal = None
        self.focus_handler = None
        self.config = Config()
        self.dialog = None

    def unload(self):
        self.disconnect_signals()
        self.terminal = None
        self.focus_handler = None
        self.dialog = None

    def callback(self, menuitems, menu, terminal):
        menuitem = gtk.MenuItem('Snippets Library')
        menuitem.connect('activate', self.on_activate, terminal)
        menuitems.append(menuitem)

    def on_activate(self, widget, terminal):
        self.terminal = terminal
        self.reconnect_signals()
        self.set_styles()
        self.dialog = MainDialog()
        self.dialog.connect('insert-command', self.on_insert_command)
        self.dialog.connect('insert-command-dialog',
                            self.on_insert_command_dialog)
        try:
            self.dialog.run()
        except Exception as error:
            ErrorDialog().run(error)

    def reconnect_signals(self):
        self.disconnect_signals()
        self.connect_signals()

    def connect_signals(self):
        self.focus_handler = gobject.add_emission_hook(
            Terminal,
            'focus-in',
            self.on_terminal_focus_in)

    def disconnect_signals(self):
        if self.focus_handler:
            gobject.remove_emission_hook(Terminal, 'focus-in',
                                         self.focus_handler)

    def set_styles(self):
        try:
            if self.config['use_system_font']:
                font = self.config.get_system_font()
            else:
                font = self.config['font']
        except:
            pass
        styles = clisnips.config.styles
        styles.font = font
        styles.bgcolor = self.terminal.bgcolor
        styles.fgcolor = self.terminal.fgcolor_active
        styles.cursor_color = self.config['cursor_color']

    # ---------- Signals ---------- #

    def on_terminal_focus_in(self, terminal):
        self.terminal = terminal
        return True

    def on_insert_command(self, dialog, command):
        self.terminal.feed(str(command))

    def on_insert_command_dialog(self, dialog):
        if self.terminal:
            cwd = self.terminal.get_cwd()
            dialog.set_cwd(cwd)
