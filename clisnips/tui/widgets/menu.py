import enum

import urwid

from .list_box import CyclingFocusListBox


class PopupMenu(urwid.WidgetWrap):
    class Signals(enum.StrEnum):
        CLOSED = enum.auto()

    signals = list(Signals)

    def __init__(self, title=''):
        self._walker = urwid.SimpleFocusListWalker([])
        lb = urwid.LineBox(
            CyclingFocusListBox(self._walker),
            title=title,
            title_align='left',
            tlcorner='┌', tline='╌', trcorner='┐',
            lline='┆', rline='┆',
            blcorner='└', bline='╌', brcorner='┘',
        )  # fmt: skip
        super().__init__(urwid.AttrMap(lb, 'popup-menu'))

    def set_items(self, items):
        self._walker[:] = items

    def append(self, item):
        self._walker.append(item)

    def keypress(self, size, key):
        if key == 'esc':
            self._emit(PopupMenu.Signals.CLOSED)
            return
        return super().keypress(size, key)

    def __len__(self):
        return len(self._walker)
