import unittest

from gi.repository import Gtk


class GtkTestCase(unittest.TestCase):

    def _refresh_gui(self):
        while Gtk.events_pending():
            Gtk.main_iteration_do(blocking=False)
