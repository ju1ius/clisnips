from typing import Generic, TypeVar
import urwid

from clisnips.tui.urwid_types import TextMarkup


V = TypeVar('V')


class Field(Generic[V]):
    signals = ['changed']

    def get_value(self) -> V:
        raise NotImplementedError()

    def set_validation_markup(self, value: TextMarkup):
        raise NotImplementedError()


class Entry(Generic[V]):
    signals = ['changed']

    def get_value(self) -> V:
        raise NotImplementedError()


class SimpleField(Field[V], urwid.Pile):
    _VALIDATION_POSITION = 2

    def __init__(self, label: TextMarkup, entry: Entry[V]):
        self._entry = entry
        urwid.connect_signal(self._entry, 'changed', lambda *w: self._emit('changed'))
        self._validation_text = urwid.Text('')
        super().__init__(
            [
                urwid.Text(label),
                self._entry,  # type: ignore
                # self._validation_text,
            ]
        )

    def get_value(self) -> V:
        return self._entry.get_value()

    def set_validation_markup(self, value: TextMarkup):
        self._validation_text.set_text(value)
        try:
            self.contents.remove((self._validation_text, ('weight', 1)))
        except ValueError:
            ...
        if value:
            self.contents.insert(self._VALIDATION_POSITION, (self._validation_text, ('weight', 1)))
