from gi.repository import Gtk

from .progress import ProgressDialog
from ..database.snippets_db import SnippetsDatabase
from ..exporters.clisnips import Exporter


def _import_snippets(db: SnippetsDatabase, filename: str, type: str):
    if type == 'CliCompanion 2':
        from ..importers.clicompanion import Importer
    else:
        from ..importers.clisnips import Importer

    def _task(fn):
        Importer(db).process(fn)

    dlg = ProgressDialog(f'Importing snippets from {filename}')
    dlg.run(_task, filename)


def _export_snippets(db: SnippetsDatabase, filename: str):
    exporter = Exporter(db)

    def _task(fn):
        exporter.export(fn)

    dlg = ProgressDialog(f'Exporting snippets to {filename}')
    dlg.run(_task, filename)


def _clisnips_xml_filter(info: Gtk.FileFilterInfo):
    return info.filename.endswith('.clisnips') or info.mime_type == 'application/xml'


def _cc2_filter(info: Gtk.FileFilterInfo):
    return info.filename.endswith('.config') and info.mime_type == 'text/plain'


class ImportDialog(Gtk.FileChooserDialog):

    def __init__(self):
        super().__init__(title='Import Snippet Database')
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        self.set_action(Gtk.FileChooserAction.OPEN)
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                         Gtk.STOCK_APPLY, Gtk.ResponseType.ACCEPT)

        xml_filter = Gtk.FileFilter()
        xml_filter.set_name('CliSnips XML')
        xml_filter.add_custom(
            Gtk.FileFilterFlags.FILENAME | Gtk.FileFilterFlags.MIME_TYPE,
            _clisnips_xml_filter
        )
        self.add_filter(xml_filter)

        cc2_filter = Gtk.FileFilter()
        cc2_filter.set_name('CliCompanion 2')
        cc2_filter.add_custom(
            Gtk.FileFilterFlags.FILENAME | Gtk.FileFilterFlags.MIME_TYPE,
            _cc2_filter
        )
        self.add_filter(cc2_filter)

    def run(self, db):
        response = super().run()
        if response != Gtk.ResponseType.ACCEPT:
            self.destroy()
            return
        name = self.get_filename()
        type = self.get_filter().get_name()
        _import_snippets(db, name, type)
        self.destroy()


class ExportDialog(Gtk.FileChooserDialog):

    def __init__(self):
        super().__init__(title='Export Snippets')
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        self.set_action(Gtk.FileChooserAction.SAVE)
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                         Gtk.STOCK_APPLY, Gtk.ResponseType.ACCEPT)
        self.set_do_overwrite_confirmation(True)

    def run(self, db):
        response = super().run()
        if response != Gtk.ResponseType.ACCEPT:
            self.destroy()
            return
        filename = self.get_filename()
        _export_snippets(db, filename)
        self.destroy()
