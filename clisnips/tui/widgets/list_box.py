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
