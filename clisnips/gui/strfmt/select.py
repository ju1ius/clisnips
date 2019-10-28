from typing import Iterable, Optional

from gi.repository import Gtk

from .field import SimpleField


OptionsType = Iterable[str]


class SelectField(SimpleField):

    def __init__(self, label: str, *args, **kwargs):
        entry = SelectEntry(*args, **kwargs)
        super().__init__(label, entry)


class SelectEntry(Gtk.ComboBox):

    def __init__(self, options: Optional[OptionsType] = None, default: int = 0):
        super().__init__()
        model = Gtk.ListStore(str)
        if options:
            for value in options:
                model.append(row=(value,))
        self.set_model(model)
        cell = Gtk.CellRendererText()
        self.pack_start(cell, expand=True)
        self.add_attribute(cell, 'text', 0)
        self.set_active(default)

    def get_value(self) -> str:
        idx = self.get_active()
        if not idx:
            return ''
        return self.get_model()[idx][0]
