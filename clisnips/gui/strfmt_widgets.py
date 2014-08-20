import os
import locale

import gtk
import glib
import gio
import gobject

from ..strfmt.doc_nodes import ValueRange, ValueList
from ..utils import get_num_decimals


def _entry_from_doc(doc):
    if not doc:
        return Entry()
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


class Field(gtk.VBox):

    __gsignals__ = {
        'changed': (gobject.SIGNAL_RUN_LAST,
                    gobject.TYPE_NONE,
                    ())
    }

    def __init__(self, label, entry):
        super(Field, self).__init__(spacing=6)
        self.label = gtk.Label()
        self.label.set_alignment(0, 0.5)
        self.label.set_markup(label)
        self.entry = entry
        self.entry.connect('changed', self._on_entry_changed)
        self.pack_start(self.label, False)
        self.pack_start(self.entry, False)

    @classmethod
    def from_documentation(klass, name, doc=None):
        """
        Builds a field instance from a strfmt.doc_nodes.Parameter object.
        """
        if not doc:
            label = '<b>{}</b>'.format(name)
        else:
            hint = '(<i>%s</i>)' % (doc.typehint) if doc.typehint else ''
            text = doc.text.strip() if doc.text else ''
            label = '<b>{name}</b> {type} {text}'.format(
                name=doc.name,
                type=hint,
                text=text
            )
        entry = _entry_from_doc(doc)
        return klass(label, entry)

    def set_sensitive(self, sensitive):
        self.entry.set_sensitive(sensitive)

    def set_editable(self, editable):
        if 'editable' in self.entry.props:
            self.entry.set_sensitive(editable)

    def get_value(self):
        return self.entry.get_value()

    def _on_entry_changed(self, entry):
        self.emit('changed')


class Entry(gtk.Entry):

    def __init__(self, default=''):
        super(Entry, self).__init__()
        if default:
            self.set_text(default)

    def get_value(self):
        return self.get_text()


class FlagEntry(gtk.CheckButton):

    __gsignals__ = {
        'changed': (gobject.SIGNAL_RUN_LAST,
                    gobject.TYPE_NONE,
                    ())
    }

    def __init__(self, flag):
        super(FlagEntry, self).__init__()
        self.flag = flag
        self.connect('toggled', lambda x: self.emit('changed'))

    def get_value(self):
        return self.flag if self.get_active() else ''


class Select(gtk.ComboBox):

    def __init__(self, options=[], default=0):
        model = gtk.ListStore(str)
        for value in options:
            model.append(row=(value,))
        super(Select, self).__init__(model)
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 0)
        self.set_active(default)

    def get_value(self):
        idx = self.get_active()
        return self.get_model()[idx][0]


class Range(gtk.SpinButton):

    def __init__(self, start, end, step, default):
        adjustment = gtk.Adjustment(lower=start, upper=end, step_incr=step)
        decimals = get_num_decimals(step)
        super(Range, self).__init__(adjustment, digits=decimals)
        self.set_snap_to_ticks(True)
        if default is not None:
            self.set_value(default)

    def get_value(self):
        if self.get_digits() == 0:
            return super(Range, self).get_value_as_int()
        return super(Range, self).get_value()


class PathEntry(gtk.HBox):

    __gsignals__ = {
        'changed': (gobject.SIGNAL_RUN_LAST,
                    gobject.TYPE_NONE,
                    ())
    }

    COLUMN_ICON, COLUMN_TEXT = range(2)
    COLUMNS = (gio.Icon, str)
    COMPLETION_TIMEOUT = 300

    MODE_PATH = 'path'
    MODE_FILE = 'file'
    MODE_DIR = 'dir'

    def __init__(self, cwd=None, mode=None, default=''):
        super(PathEntry, self).__init__(spacing=6)
        self._filechooser = None
        self._mode = mode or self.MODE_FILE
        self.show_files = self._mode in (self.MODE_PATH, self.MODE_FILE)
        self._entry = gtk.Entry()
        if default:
            self._entry.set_text(default)
        self._setup_completion()
        self._completion_timeout = 0
        self.set_cwd(cwd)

    def get_value(self):
        return self._entry.get_text()

    def set_cwd(self, cwd=None):
        self._cwd = cwd or os.getcwd()
        if self._filechooser:
            self._filechooser.set_current_folder(self._cwd)

    def _setup_completion(self):
        # setup text entry
        self._entry.connect("changed", self._on_entry_changed)
        self.pack_start(self._entry, True, True, 0)
        # setup completion
        self._completion = gtk.EntryCompletion()
        self._model = gtk.ListStore(*self.COLUMNS)
        self._completion.set_model(self._model)
        pixbuf_cell = gtk.CellRendererPixbuf()
        self._completion.pack_start(pixbuf_cell, expand=False)
        self._completion.add_attribute(pixbuf_cell, 'gicon', self.COLUMN_ICON)
        self._completion.set_text_column(self.COLUMN_TEXT)
        self._entry.set_completion(self._completion)
        # setup filechooser
        if self._mode in (self.MODE_FILE, self.MODE_DIR):
            self._filechooser = gtk.FileChooserButton('')
            if self._mode == self.MODE_FILE:
                title = 'Select a file'
                action = gtk.FILE_CHOOSER_ACTION_OPEN
            elif self._mode == self.MODE_DIR:
                title = 'Select a folder'
                action = gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER
            self._filechooser.set_title(title)
            self._filechooser.set_action(action)
            self._filechooser.connect('file-set',
                                      self._on_filechooser_file_set)
            self.pack_start(self._filechooser, False, True, 0)

    def _on_entry_changed(self, entry):
        if self._completion_timeout:
            glib.source_remove(self._completion_timeout)
        self._completion_timeout = glib.timeout_add(
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
        if not text:
            return False
        self._completion.set_model(None)
        self._model.clear()
        for filepath, filetype in self._get_completions(text):
            gicon = gio.content_type_get_icon(filetype)
            self._model.append((gicon, filepath))
        self._completion.set_model(self._model)
        return False

    def _get_completions(self, text):
        dirname, basename = os.path.split(text)
        if dirname and dirname[0] == '~':
            realpath = os.path.expanduser(dirname)
        elif dirname and dirname[0] == '/':
            realpath = dirname
        else:
            realpath = os.path.join(self._cwd, dirname)
        if not os.path.exists(realpath):
            return
        for fn, ft in self._listdir(realpath):
            if fn.startswith(basename):
                yield (os.path.join(dirname, fn), ft)

    def _listdir(self, path):
        dirs, files = [], []
        for fn in os.listdir(path):
            fp = os.path.join(path, fn)
            if os.path.isdir(fp):
                dirs.append((fn, 'inode/directory'))
            elif self.show_files and os.path.isfile(fp):
                ft = gio.content_type_guess(fp)
                files.append((fn, ft))
        dirs = sorted(dirs, key=self._sort)
        if self.show_files:
            return dirs + sorted(files, key=self._sort)
        return dirs

    def _sort(self, item):
        return locale.strxfrm(item[0])
