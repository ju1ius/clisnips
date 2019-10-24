import locale
import os
from pathlib import Path

from gi.repository import GLib, GObject, Gio, Gtk

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

    COLUMN_ICON, COLUMN_TEXT = range(2)
    COLUMNS = (Gio.Icon, str)
    COMPLETION_TIMEOUT = 300

    MODE_PATH = 'path'
    MODE_FILE = 'file'
    MODE_DIR = 'dir'

    def __init__(self, cwd=None, mode=None, default=''):
        super().__init__(spacing=6)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self._filechooser = None
        self._cwd: Path = Path(cwd) if cwd is not None else Path.cwd()
        self._mode = mode or self.MODE_FILE
        self.show_files = self._mode in (self.MODE_PATH, self.MODE_FILE)
        self._completion_timeout = 0

        # setup text entry
        self._entry = Gtk.Entry()
        if default:
            self._entry.set_text(default)
        self.pack_start(self._entry, expand=True, fill=True, padding=0)
        self._entry.connect("changed", self._on_entry_changed)

        # setup filechooser
        if self._mode in (self.MODE_FILE, self.MODE_DIR):
            self._filechooser = Gtk.FileChooserButton('')
            if self._mode == self.MODE_FILE:
                title = 'Select a file'
                action = Gtk.FileChooserAction.OPEN
            else:
                title = 'Select a folder'
                action = Gtk.FileChooserAction.SELECT_FOLDER
            self._filechooser.set_title(title)
            self._filechooser.set_action(action)
            self._filechooser.set_current_folder(str(self._cwd))
            self._filechooser.connect('file-set', self._on_filechooser_file_set)
            self.pack_start(self._filechooser, expand=False, fill=True, padding=0)

        # setup completion
        self._completion = PathCompletion(self._cwd, self.show_files)
        self._entry.set_completion(self._completion)

    def get_value(self):
        return self._entry.get_text()

    def set_cwd(self, cwd=None):
        self._cwd = Path(cwd) if cwd is not None else Path.cwd()
        self._completion.set_cwd(self._cwd)
        if self._filechooser:
            self._filechooser.set_current_folder(str(self._cwd))

    def _on_entry_changed(self, entry):
        if self._completion_timeout:
            GLib.source_remove(self._completion_timeout)
        self._completion_timeout = GLib.timeout_add(
            self.COMPLETION_TIMEOUT,
            self._on_completion_timeout
        )

    def _on_filechooser_file_set(self, btn):
        selected = self._filechooser.get_filename()
        if selected:
            self._entry.set_text(selected)

    def _on_completion_timeout(self):
        self._completion_timeout = 0
        self.emit('changed')

        text = self._entry.get_text()
        if text:
            self._completion.get_matches(text)
        return False

    def _get_completions(self, text):
        path = Path(text).expanduser()
        if not path.is_absolute():
            path = self._cwd / path
        if not path.parent.exists():
            return
        for fp in path.parent.glob(f'{path.name}*'):
            if fp.is_dir():
                yield fp, 'inode/directory'
            elif self.show_files and fp.is_file():
                ft, uncertain = Gio.content_type_guess(str(fp))
                yield fp, ft
        # yield from self._glob(path.parent, f'{path.name}*')

    def _glob(self, path: Path, pattern: str):
        dirs, files = [], []
        for fp in path.glob(pattern):
            if fp.is_dir():
                dirs.append((fp, 'inode/directory'))
            elif self.show_files and fp.is_file():
                ft, uncertain = Gio.content_type_guess(str(fp))
                files.append((fp, ft))
        dirs = sorted(dirs, key=self._sort)
        print(dirs, files)
        if self.show_files:
            yield from iter(dirs + sorted(files, key=self._sort))
        yield from iter(dirs)

    def _sort(self, item):
        return locale.strxfrm(str(item[0]))


class PathCompletion(Gtk.EntryCompletion):

    COLUMN_ICON, COLUMN_NAME, COLUMN_PATH = range(3)
    COLUMNS = (Gio.Icon, str, str)

    def __init__(self, cwd, show_files=True):
        super().__init__()
        self._cwd = cwd
        self._show_files = show_files
        self.set_model(Gtk.ListStore(*self.COLUMNS))
        self.set_match_func(self._match_func, {'foo': 'bar'})
        pixbuf_cell = Gtk.CellRendererPixbuf()
        self.pack_start(pixbuf_cell, expand=False)
        self.add_attribute(pixbuf_cell, 'gicon', self.COLUMN_ICON)
        text_cell = Gtk.CellRendererText()
        self.pack_start(text_cell, expand=False)
        self.add_attribute(text_cell, 'text', self.COLUMN_NAME)
        # self.set_text_column(self.COLUMN_NAME)
        # self.connect('match-selected', self._on_match_selected)

    def set_cwd(self, cwd):
        self._cwd = Path(cwd) if cwd is not None else Path.cwd()

    def get_matches(self, text: str):
        model = self.get_model()
        model.clear()
        for name, path, mime_type in self._get_completions(text):
            model.append((
                Gio.content_type_get_icon(mime_type),
                name,
                path
            ))

    def _get_completions(self, text):
        path = os.path.expanduser(text)
        if not os.path.isabs(path):
            path = os.path.join(self._cwd, path)
        dirname, basename = os.path.split(path)
        if not os.path.exists(dirname):
            return
        if path.endswith('/') and os.path.isdir(path):
            entries = os.scandir(path)
        else:
            entries = (f for f in os.scandir(dirname) if f.name.lower().startswith(basename.lower()))
        for entry in sorted(entries, key=self._sort_entries):
            if entry.is_dir():
                yield entry.name, entry.path, 'inode/directory'
            elif self._show_files and entry.is_file():
                ft, uncertain = Gio.content_type_guess(entry.path)
                yield entry.name, entry.path, ft

    @staticmethod
    def _match_func(completion, key, tree_iter, data=None):
        # print(f'Match func: {key} ({self.get_entry().get_text()})')
        return True

    def do_match_selected(self, model, tree_iter):
        path = model.get_value(tree_iter, self.COLUMN_PATH)
        entry: Gtk.Entry = self.get_entry()
        entry.set_text(path)
        entry.set_position(len(path))

        return True

    @staticmethod
    def _sort_entries(entry):
        return locale.strxfrm(entry.name)
