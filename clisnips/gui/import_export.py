import gtk

from .progress import ProgressDialog
from ..exporters.clisnips import Exporter


class ImportDialog(gtk.FileChooserDialog):

    def __init__(self):
        super(ImportDialog, self).__init__(title='Import Snippet Database')
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        self.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
        self.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                         gtk.STOCK_APPLY, gtk.RESPONSE_ACCEPT)

        xml_filter = gtk.FileFilter()
        xml_filter.set_name('CliSnips XML')
        xml_filter.add_custom(
            gtk.FILE_FILTER_DISPLAY_NAME | gtk.FILE_FILTER_MIME_TYPE,
            self.xml_filter_func
        )
        self.add_filter(xml_filter)

        cc2_filter = gtk.FileFilter()
        cc2_filter.set_name('CliCompanion 2')
        cc2_filter.add_custom(
            gtk.FILE_FILTER_DISPLAY_NAME | gtk.FILE_FILTER_MIME_TYPE,
            self.cc2_filter_func
        )
        self.add_filter(cc2_filter)

    def run(self, db):
        response = super(ImportDialog, self).run()
        if response != gtk.RESPONSE_ACCEPT:
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
        importer = Importer(db)
        
        def _task(filename):
            importer.import_file(filename)

        msg = 'Importing snippets from %s' % filename
        dlg = ProgressDialog(msg).run(_task, filename)

    def xml_filter_func(self, filter_info):
        path, uri, name, mimetype = filter_info
        return name.endswith('.clisnips') and mimetype == 'application/xml'

    def cc2_filter_func(self, filter_info):
        path, uri, name, mimetype = filter_info
        return name.endswith('.config') and mimetype == 'text/plain'


class ExportDialog(gtk.FileChooserDialog):

    def __init__(self):
        super(ExportDialog, self).__init__(title='Export Snippets')
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        self.set_action(gtk.FILE_CHOOSER_ACTION_SAVE)
        self.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                         gtk.STOCK_APPLY, gtk.RESPONSE_ACCEPT)
        self.set_do_overwrite_confirmation(True)

    def run(self, db):
        response = super(ExportDialog, self).run()
        if response != gtk.RESPONSE_ACCEPT:
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
