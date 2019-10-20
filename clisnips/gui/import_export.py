from gi.repository import Gtk

from .progress import ProgressDialog
from ..exporters.clisnips import Exporter


class ImportDialog(Gtk.FileChooserDialog):

    def __init__(self):
        super(ImportDialog, self).__init__(title='Import Snippet Database')
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        self.set_action(Gtk.FileChooserAction.OPEN)
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                         Gtk.STOCK_APPLY, Gtk.ResponseType.ACCEPT)

        xml_filter = Gtk.FileFilter()
        xml_filter.set_name('CliSnips XML')
        xml_filter.add_custom(
            Gtk.FILE_FILTER_DISPLAY_NAME | Gtk.FILE_FILTER_MIME_TYPE,
            self.xml_filter_func
        )
        self.add_filter(xml_filter)

        cc2_filter = Gtk.FileFilter()
        cc2_filter.set_name('CliCompanion 2')
        cc2_filter.add_custom(
            Gtk.FILE_FILTER_DISPLAY_NAME | Gtk.FILE_FILTER_MIME_TYPE,
            self.cc2_filter_func
        )
        self.add_filter(cc2_filter)

    def run(self, db):
        response = super(ImportDialog, self).run()
        if response != Gtk.ResponseType.ACCEPT:
            self.destroy()
            return
        name = self.get_filename()
        type = self.get_filter().get_name()
        self._import(db, name, type)
        self.destroy()

    def _import(self, db, filename, type):
        if type == 'CliCompanion 2':
            from ..importers.clicompanion import Importer
        else:
            from ..importers.clisnips import Importer

        def _task(filename):
            Importer(db).process(filename)

        msg = 'Importing snippets from %s' % filename
        dlg = ProgressDialog(msg).run(_task, filename)

    def xml_filter_func(self, filter_info):
        path, uri, name, mimetype = filter_info
        return name.endswith('.clisnips') or mimetype == 'application/xml'

    def cc2_filter_func(self, filter_info):
        path, uri, name, mimetype = filter_info
        return name.endswith('.config') and mimetype == 'text/plain'


class ExportDialog(Gtk.FileChooserDialog):

    def __init__(self):
        super(ExportDialog, self).__init__(title='Export Snippets')
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        self.set_action(Gtk.FileChooserAction.SAVE)
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                         Gtk.STOCK_APPLY, Gtk.ResponseType.ACCEPT)
        self.set_do_overwrite_confirmation(True)

    def run(self, db):
        response = super(ExportDialog, self).run()
        if response != Gtk.ResponseType.ACCEPT:
            self.destroy()
            return
        filename = self.get_filename()
        self._export(db, filename)
        self.destroy()

    def _export(self, db, filename):
        exporter = Exporter(db)

        def _task(filename):
            exporter.export(filename)

        msg = 'Exporting snippets to %s' % filename
        dlg = ProgressDialog(msg).run(_task, filename)
