import os
import unittest

from clisnips import config
from clisnips.database.snippets_db import SnippetsDatabase
from clisnips.gui.main_dialog import MainDialog
from gui_testcase import GtkTestCase

fixtures = [
    {'title': '', 'cmd': '', 'doc': '', 'tag': ''}
]


class MainDialogTest(GtkTestCase):

    @classmethod
    def setUpClass(cls):
        config.database_path = ':memory:'
        db = SnippetsDatabase(config.database_path).open()
        for row in fixtures:
            db.insert(row)

    def setUp(self):
        self._window = MainDialog()
        self._window.set_cwd(os.getcwd())
        self._window.run()

    def tearDown(self):
        self._window.destroy()

    def assertListContainsRows(self, rows):
        pass

    def testWindowLaunches(self):
        pass

