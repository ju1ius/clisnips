import gtk

from ..database.snippets_db import SnippetsDatabase
from .progress import ProgressDialog



class SqliteFilter(gtk.FileFilter):

    def __init__(self):
        super(SqliteFilter, self).__init__()
        self.set_name('CliSnips Database')
        self.add_mime_type('application/x-sqlite3')


class OpenDialog(gtk.FileChooserDialog):

    def __init__(self):
        super(OpenDialog, self).__init__(title='Open Snippets Database')
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        self.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
        self.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                         gtk.STOCK_APPLY, gtk.RESPONSE_ACCEPT)

        self.add_filter(SqliteFilter())

    def run(self):
        response = super(OpenDialog, self).run()
        if response != gtk.RESPONSE_ACCEPT:
            self.destroy()
            return
        filename = self.get_filename()
        self.destroy()
        return filename


class CreateDialog(gtk.FileChooserDialog):

    def __init__(self):
        super(CreateDialog, self).__init__(title='Create Snippets Database')
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_do_overwrite_confirmation(True)

        self.set_action(gtk.FILE_CHOOSER_ACTION_SAVE)
        self.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                         gtk.STOCK_APPLY, gtk.RESPONSE_ACCEPT)

        self.add_filter(SqliteFilter())

    def run(self):
        response = super(CreateDialog, self).run()
        if response != gtk.RESPONSE_ACCEPT:
            self.destroy()
            return
        filename = self.get_filename()
        if not filename.endswith('.sqlite'):
            filename += '.sqlite'
        self.destroy()
        return filename
