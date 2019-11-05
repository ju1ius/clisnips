from gi.repository import GObject, Gtk

from .field import Field


# @Field()
class FlagField(Field, Gtk.Box):

    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_LAST, None, ())
    }

    def __init__(self, label: str, *args, **kwargs):
        Field.__init__(self)
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL)
        self.set_spacing(6)
        self.set_baseline_position(Gtk.BaselinePosition.CENTER)

        self.entry = FlagEntry(*args, **kwargs)
        self.entry.set_valign(Gtk.Align.CENTER)
        self.pack_start(self.entry, expand=False, fill=True, padding=0)

        self.label = Gtk.Label()
        # self.label.set_valign(Gtk.Align.START)
        self.label.set_line_wrap_mode(Gtk.WrapMode.WORD)
        self.label.set_max_width_chars(100)
        self.label.set_markup(label)
        self.pack_start(self.label, expand=False, fill=True, padding=0)

        self.entry.connect('changed', lambda *w: self.emit('changed'))


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

