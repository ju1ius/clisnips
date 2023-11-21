import enum
from collections.abc import Iterable
from typing import Generic, TypeVar

import urwid

from .menu import PopupMenu

__all__ = ['ComboBox']

from .radio import RadioItem, RadioState

V = TypeVar('V')


class Select(PopupMenu, Generic[V]):
    class Signals(enum.StrEnum):
        CHANGED = enum.auto()

    signals = PopupMenu.signals + list(Signals)

    def __init__(self):
        self._group: list[RadioItem[V]] = []
        self._selected_item: RadioItem[V] | None = None
        super().__init__()

    def set_choices(self, choices: Iterable[tuple[str, V, bool]]):
        self._walker.clear()
        for choice in choices:
            self.append_choice(*choice)

    def append_choice(self, label: str, value: V, selected: bool = False):
        item = RadioItem(self._group, label, value, selected)
        urwid.connect_signal(item, 'change', self._on_item_changed)
        if selected:
            self._selected_item = item
        super().append(item)

    def get_selected(self) -> RadioItem[V] | None:
        return self._selected_item

    def get_default(self) -> RadioItem[V] | None:
        if not len(self):
            return None
        for item, _ in self._walker:
            if item.get_state() is True:
                return item
        return self._walker[0]

    def _on_item_changed(self, item: RadioItem[V], state: RadioState):
        if state is True:
            self._selected_item = item
            self._emit(self.Signals.CHANGED, item)


class ComboBoxButton(urwid.Button):
    button_left = urwid.Text('▼')
    button_right = urwid.Text('▼')


class ComboBox(urwid.PopUpLauncher, Generic[V]):
    class Signals(enum.StrEnum):
        CHANGED = 'changed'

    signals = list(Signals)

    def __init__(self):
        self._select: Select[V] = Select()
        urwid.connect_signal(self._select, 'closed', lambda *x: self.close_pop_up())
        urwid.connect_signal(self._select, 'changed', self._on_selection_changed)

        self._button = ComboBoxButton('Select an item')

        super().__init__(self._button)
        urwid.connect_signal(self.original_widget, 'click', lambda *x: self.open_pop_up())

    def set_items(self, items):
        self._select.set_choices(items)
        default = self._select.get_default()
        if default:
            self._button.set_label(default.get_label())

    def append(self, label: str, value: V, selected=False):
        self._select.append_choice(label, value, selected)
        if selected:
            self._button.set_label(label)

    def create_pop_up(self) -> Select[V]:
        return self._select

    def get_pop_up_parameters(self):
        return {'left': 0, 'top': 0, 'overlay_width': 32, 'overlay_height': len(self._select) + 2}

    def get_selected(self) -> V | None:
        item = self._select.get_selected()
        if item is not None:
            return item.get_value()

    def _on_selection_changed(self, menu, item: RadioItem[V]):
        self._button.set_label(item.get_label())
        self.close_pop_up()
        self._emit(self.Signals.CHANGED, item.get_value())
