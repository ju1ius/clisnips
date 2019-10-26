from pathlib import Path

from gi.repository import GObject, Gtk

from .path_entry import PathEntry as _PathEntry
from ..strfmt.doc_nodes import ValueList, ValueRange
from ..utils.number import get_num_decimals


def _entry_from_doc(field: str, doc):
    if not doc:
        return FlagEntry(field) if field.startswith('-') else Entry()
    typehint = doc.typehint
    valuehint = doc.valuehint
    default = ''
    if isinstance(valuehint, ValueRange):
        return Range(
            valuehint.start,
            valuehint.end,
            valuehint.step,
            valuehint.default
        )
    if isinstance(valuehint, ValueList):
        if len(valuehint) > 1:
            return Select(valuehint.values, valuehint.default)
        default = str(valuehint.values[0])
    if typehint in ('path', 'file', 'dir'):
        return PathEntry(mode=typehint, default=default)
    if typehint == 'flag':
        return FlagEntry(doc.name)
    return Entry(default=default)


class Field(Gtk.Box):

    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_LAST, None, ())
    }

    def __init__(self, label: str, entry: Gtk.Widget):
        super().__init__(spacing=6, orientation=Gtk.Orientation.VERTICAL)
        self.label = Gtk.Label()
        self.label.set_alignment(0, 0.5)
        self.label.set_markup(label)
        self.entry = entry
        self.entry.connect('changed', self._on_entry_changed)
        self.pack_start(self.label, expand=False, fill=True, padding=0)
        self.pack_start(self.entry, expand=False, fill=False, padding=0)

    @classmethod
    def from_documentation(cls, name, doc=None):
        """
        Builds a field instance from a strfmt.doc_nodes.Parameter object.
        """
        if not doc:
            label = f'<b>{name}</b>'
        else:
            hint = f'(<i>{doc.typehint}</i>)' if doc.typehint else ''
            text = doc.text.strip() if doc.text else ''
            label = f'<b>{doc.name}</b> {hint} {text}'
        entry = _entry_from_doc(name, doc)
        return cls(label, entry)

    def set_sensitive(self, sensitive):
        self.entry.set_sensitive(sensitive)

    def set_editable(self, editable):
        if 'editable' in self.entry.props:
            self.entry.set_sensitive(editable)

    def get_value(self):
        return self.entry.get_value()

    def _on_entry_changed(self, entry):
        self.emit('changed')


class Entry(Gtk.Entry):

    def __init__(self, default=''):
        super().__init__()
        if default:
            self.set_text(default)

    def get_value(self):
        return self.get_text()


class FlagEntry(Gtk.Switch):

    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_LAST, None, ())
    }

    def __init__(self, flag):
        super().__init__()
        self.flag = flag
        self.connect('state-set', lambda w, s: self.emit('changed'))

    def get_value(self):
        return self.flag if self.get_active() else ''


class Select(Gtk.ComboBox):

    def __init__(self, options=None, default=0):
        super().__init__()
        model = Gtk.ListStore(str)
        for value in options:
            model.append(row=(value,))
        self.set_model(model)
        cell = Gtk.CellRendererText()
        self.pack_start(cell, expand=True)
        self.add_attribute(cell, 'text', 0)
        self.set_active(default)

    def get_value(self):
        idx = self.get_active()
        return self.get_model()[idx][0]


class Range(Gtk.SpinButton):

    def __init__(self, start, end, step, default):
        adjustment = Gtk.Adjustment(lower=start, upper=end, step_incr=step)
        decimals = get_num_decimals(step)
        super().__init__(adjustment, digits=decimals)
        self.set_snap_to_ticks(True)
        if default is not None:
            self.set_value(default)

    def get_value(self):
        if self.get_digits() == 0:
            return super().get_value_as_int()
        return super().get_value()


class PathEntry(Gtk.Box):

    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_LAST, None, ())
    }

    MODE_PATH = 'path'
    MODE_FILE = 'file'
    MODE_DIR = 'dir'

    def __init__(self, cwd=None, mode=None, default=''):
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
