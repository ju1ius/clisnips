from gi.repository import Gtk

from .field import SimpleField


class TextField(SimpleField):

    def __init__(self, label: str, *args, **kwargs):
        entry = TextEntry(*args, **kwargs)
        super().__init__(label, entry)


class TextEntry(Gtk.Entry):

    def __init__(self, default: str = ''):
        super().__init__()
        self.set_text(default)

    def get_value(self) -> str:
        return self.get_text()
