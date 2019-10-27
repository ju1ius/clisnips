from gi.repository import Gtk
from gi.repository import GObject


class Field:

    entry: Gtk.Widget

    def set_sensitive(self, sensitive):
        self.entry.set_sensitive(sensitive)

    def set_editable(self, editable):
        if 'editable' in self.entry.props:
            self.entry.set_sensitive(editable)

    def get_value(self):
        return self.entry.get_value()


class SimpleField(Field, Gtk.Box):

    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_LAST, None, ())
    }

    def __init__(self, label: str, entry: Gtk.Widget):
        Field.__init__(self)
        Gtk.Box.__init__(self)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(6)

        self.label = Gtk.Label()
        self.label.set_alignment(0, 0.5)
        self.label.set_markup(label)
        self.pack_start(self.label, expand=False, fill=True, padding=0)

        self.entry = entry
        self.pack_start(entry, expand=False, fill=False, padding=0)
        self.entry.connect('changed', lambda *w: self.emit('changed'))
