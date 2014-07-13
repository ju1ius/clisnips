import unittest

import gtk


class GtkTestCase(unittest.TestCase):

    def _refresh_gui(self):
        while gtk.events_pending():
            gtk.main_iteration(block=False)
