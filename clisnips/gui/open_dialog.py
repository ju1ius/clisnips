from gi.repository import Gtk


class SqliteFilter(Gtk.FileFilter):

    def __init__(self):
        super(SqliteFilter, self).__init__()
        self.set_name('CliSnips Database')
        self.add_mime_type('application/x-sqlite3')


class OpenDialog(Gtk.FileChooserDialog):

    def __init__(self):
        super(OpenDialog, self).__init__(title='Open Snippets Database')
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        self.set_action(Gtk.FileChooserAction.OPEN)
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                         Gtk.STOCK_APPLY, Gtk.ResponseType.ACCEPT)

        self.add_filter(SqliteFilter())

    def run(self):
        response = super(OpenDialog, self).run()
        if response != Gtk.ResponseType.ACCEPT:
            self.destroy()
            return
        filename = self.get_filename()
        self.destroy()
        return filename


class CreateDialog(Gtk.FileChooserDialog):

    def __init__(self):
        super(CreateDialog, self).__init__(title='Create Snippets Database')
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_do_overwrite_confirmation(True)

        self.set_action(Gtk.FileChooserAction.SAVE)
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                         Gtk.STOCK_APPLY, Gtk.ResponseType.ACCEPT)

        self.add_filter(SqliteFilter())

    def run(self):
        response = super(CreateDialog, self).run()
        if response != Gtk.ResponseType.ACCEPT:
            self.destroy()
            return
        filename = self.get_filename()
        if not filename.endswith('.sqlite'):
            filename += '.sqlite'
        self.destroy()
        return filename
