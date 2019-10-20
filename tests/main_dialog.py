#! /usr/bin/env python
# coding=utf8
import os
import sys
from os.path import abspath, dirname, join
import gtk

#gtk.gdk.threads_init()

__dir__ = dirname(abspath(__file__))
sys.path.insert(0, join(__dir__, '..'))

from clisnips.config import config
from clisnips.database.snippets_db import SnippetsDatabase
from clisnips.gui.main_dialog import MainDialog


def on_insert_snippet(window, snippet):
    print 'CliSnips::insert-snippet "%s"' % snippet


if __name__ == "__main__":

    config.database_path = join(__dir__, 'tmp.sqlite')

    dlg = MainDialog()
    dlg.set_cwd(os.getcwd())
    dlg.connect('close', gtk.main_quit)
    dlg.connect('insert-snippet', on_insert_snippet)
    dlg.run()
    gtk.main()
