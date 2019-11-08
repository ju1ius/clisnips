import urwid

from ...urwid_types import TextMarkup


class Field:

    signals = ['changed']

    def get_value(self):
        raise NotImplementedError()


class Entry:

    signals = ['changed']

    def get_value(self):
        raise NotImplementedError()


class SimpleField(Field, urwid.Pile):

    def __init__(self, label: TextMarkup, entry: Entry):
        self._entry = entry
        urwid.connect_signal(self._entry, 'changed', lambda *w: self._emit('changed'))
        super().__init__([
            urwid.Text(label),
            self._entry
        ])

    def get_value(self):
        return self._entry.get_value()
