import urwid


class CyclingFocusListBox(urwid.ListBox):

    def keypress(self, size, key):
        if key == 'down' and self.focus_position == len(self._body) - 1:
            self.focus_position = 0
            self.set_focus_valign('top')
            return
        if key == 'up' and self.focus_position == 0:
            self.focus_position = len(self._body) - 1
            self.set_focus_valign('bottom')
            return
        return super().keypress(size, key)


class PopupMenu(urwid.WidgetWrap):

    signals = ['closed']

    def __init__(self, title=''):
        self._walker = urwid.SimpleFocusListWalker([])
        lb = urwid.LineBox(
            CyclingFocusListBox(self._walker),
            title=title, title_align='left',
            tlcorner='┌', tline='╌', trcorner='┐',
            lline='┆', rline='┆',
            blcorner='└', bline='╌', brcorner='┘'
        )
        super().__init__(urwid.AttrMap(lb, 'popup-menu'))

    def set_items(self, items):
        self._walker[:] = items

    def append(self, item):
        self._walker.append(item)

    def keypress(self, size, key):
        if key == 'esc':
            self._emit('closed')
            return
        return super().keypress(size, key)

    def __len__(self):
        return len(self._walker)
