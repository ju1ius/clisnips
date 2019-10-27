from pathlib import Path
from typing import Optional

from gi.repository import GObject, Gtk

from .field import SimpleField
from ..path_entry import PathEntry as _PathEntry
from ..._types import AnyPath


class PathField(SimpleField):

    def __init__(self, label: str, *args, **kwargs):
        entry = PathEntry(*args, **kwargs)
        super().__init__(label, entry)


class PathEntry(Gtk.Box):

    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_LAST, None, ())
    }

    MODE_PATH = 'path'
    MODE_FILE = 'file'
    MODE_DIR = 'dir'

    def __init__(self, cwd: Optional[AnyPath] = None, mode: str = '', default: str = ''):
        super().__init__(spacing=6)
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self._file_chooser = None
        self._cwd: Path = Path(cwd) if cwd is not None else Path.cwd()
        self._mode = mode or self.MODE_FILE
        self.show_files = self._mode in (self.MODE_PATH, self.MODE_FILE)
        self._completion_timeout = 0

        # setup text entry
        self._entry = _PathEntry()
        if default:
            self._entry.set_text(default)
        self.pack_start(self._entry, expand=True, fill=True, padding=0)

        # setup filechooser
        if self._mode in (self.MODE_FILE, self.MODE_DIR):
            self._file_chooser = Gtk.FileChooserButton('')
            if self._mode == self.MODE_FILE:
                title = 'Select a file'
                action = Gtk.FileChooserAction.OPEN
            else:
                title = 'Select a folder'
                action = Gtk.FileChooserAction.SELECT_FOLDER
            self._file_chooser.set_title(title)
            self._file_chooser.set_action(action)
            self._file_chooser.set_current_folder(str(self._cwd))
            self._file_chooser.connect('file-set', self._on_file_chooser_file_set)
            self.pack_start(self._file_chooser, expand=False, fill=True, padding=0)

    def get_value(self):
        return self._entry.get_text()

    def set_cwd(self, cwd=None):
        self._entry.set_working_directory(cwd)
        if self._file_chooser:
            self._file_chooser.set_current_folder(str(self._cwd))

    def _on_file_chooser_file_set(self, btn):
        selected = self._file_chooser.get_filename()
        if selected:
            self._entry.set_text(selected)
