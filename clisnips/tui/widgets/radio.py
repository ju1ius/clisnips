import enum
from collections.abc import Iterator
from typing import Generic, Hashable, Optional, TypeVar

import urwid

V = TypeVar('V', bound=Hashable)


class RadioItem(urwid.RadioButton, Generic[V]):

    def __init__(self, group: list, label: str, value: V, selected: bool = False):
        super().__init__(group, label, state=selected)
        self._value = value

    def get_value(self) -> V:
        return self._value


class RadioGroup(Generic[V]):

    class Signals(enum.StrEnum):
        CHANGED = 'changed'

    def __init__(self, choices: dict[V, str]):
        self._group: list[RadioItem[V]] = []
        for value, label in choices.items():
            item = RadioItem(self._group, label, value)
            urwid.connect_signal(item, 'change', self._on_item_clicked)

    def get_value(self) -> Optional[V]:
        for item in self._group:
            if item.get_state():
                return item.get_value()
        return None

    def set_value(self, value: V):
        for item in self._group:
            item.set_state(value == item.get_value(), do_callback=False)

    def _on_item_clicked(self, item, selected):
        if selected:
            urwid.emit_signal(self, self.Signals.CHANGED, item.get_value())

    def __iter__(self) -> Iterator[RadioItem[V]]:
        return iter(self._group)


urwid.register_signal(RadioGroup, list(RadioGroup.Signals))
