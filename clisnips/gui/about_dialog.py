from gi.repository import Gtk

from ..config import VERSION, AUTHORS, LICENSE


class AboutDialog(Gtk.AboutDialog):

    def __init__(self):
        super().__init__()
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        self.set_program_name('CliSnips')
        self.set_website('https://github.com/ju1ius/clisnips')
        self.set_version(VERSION)
        self.set_authors(AUTHORS)
        self.set_license(LICENSE)
