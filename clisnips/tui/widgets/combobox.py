from itertools import cycle
from typing import Any, Optional

import urwid
from urwid.command_map import command_map

__all__ = ['ComboBox']


class RadioItem(urwid.RadioButton):

    def __init__(self, group: list, label: str, value: Any, selected: bool = False):
        super().__init__(group, label, state=selected)
        self._value = value

    def get_value(self):
        return self._value


class Select(urwid.WidgetWrap):
    """A menu shown when parent is activated"""
    signals = ['closed', 'changed']

    def __init__(self):
        """Initialize items list"""
        self._group = []
        self._selected_item = None
        self._nav_search_key = None
        self._nav_iter = cycle([])
        self._list = urwid.Pile([])
        wrap = urwid.AttrWrap(urwid.Filler(urwid.LineBox(self._list)), 'selectable', 'combobox-bg')
        super().__init__(wrap)

    def keypress(self, size, key):
        if key == 'esc':
            self._emit('closed')
            return
        try:
            nf = next(self._nav_iter)
        except StopIteration:
            return super().keypress(size, key)
        else:
            self._list.set_focus(self._list.contents[nf][0])
        return super().keypress(size, key)

    def set_items(self, items):
        self._list.contents.clear()
        for item in items:
            self.append(*item)

    def append(self, label: str, value, selected: bool = False):
        item = RadioItem(self._group, label, value, selected)
        urwid.connect_signal(item, 'change', self._on_item_changed)
        self._list.contents.append((item, ('pack', None)))
        if selected:
            self._selected_item = item

    def get_selected(self) -> Optional[RadioItem]:
        return self._selected_item

    def get_default(self) -> Optional[RadioItem]:
        if not len(self):
            return None
        for item, _ in self._list.contents:
            if item.get_state() is True:
                return item
        return self._list.contents[0]

    def __len__(self):
        return len(self._list.contents)

    def _on_item_changed(self, item, state):
        if state is True:
            self._selected_item = item
            self._emit('changed', item)


class ComboBoxButton(urwid.Button):
    button_left = urwid.Text('▼')
    button_right = urwid.Text('▼')


class ComboBox(urwid.PopUpLauncher):

    signals = ['changed']

    def __init__(self):
        self._select = Select()
        urwid.connect_signal(self._select, 'closed', lambda *x: self.close_pop_up())
        urwid.connect_signal(self._select, 'changed', self._on_selection_changed)

        self._button = ComboBoxButton('Select an item')

        super().__init__(self._button)
        urwid.connect_signal(self.original_widget, 'click', lambda *x: self.open_pop_up())

    def set_items(self, items):
        self._select.set_items(items)
        default = self._select.get_default()
        if default:
            self._button.set_label(default.get_label())

    def append(self, label, value, selected=False):
        self._select.append(label, value, selected)
        if selected:
            self._button.set_label(self._select.get_selected().get_label())

    def create_pop_up(self):
        return self._select

    def get_pop_up_parameters(self):
        return {
            'left': 0, 'top': 0,
            'overlay_width': 32,
            'overlay_height': len(self._select) + 2
        }

    def get_selected(self):
        item = self._select.get_selected()
        if item:
            return item.get_value()

    def _on_selection_changed(self, menu, item):
        self._button.set_label(item.get_label())
        self.close_pop_up()
        self._emit('changed', item.get_value())
