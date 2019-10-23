#! /usr/bin/env python3

import os
import sys
from os.path import abspath, dirname, join

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')

from gi.repository import Gtk

__dir__ = dirname(abspath(__file__))
sys.path.insert(0, join(__dir__, '..'))

from clisnips.config import config
from clisnips.gui.app_window import AppWindow




def on_insert_snippet(window, snippet):
    print('CliSnips::insert-snippet "%s"' % snippet)


if __name__ == "__main__":

    config.database_path = join(__dir__, 'tmp.sqlite')

    dlg = AppWindow()
    dlg.set_cwd(os.getcwd())
    dlg.connect('close', Gtk.main_quit)
    dlg.connect('insert-snippet', on_insert_snippet)
    dlg.run()
    Gtk.main()
