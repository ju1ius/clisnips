import urwid


class CyclingFocusListBox(urwid.ListBox):
    def keypress(self, size: tuple[int, int], key: str):
        match (key, self.focus_position):
            case ('up' | 'k', 0):
                self.focus_position = len(self) - 1
                self.set_focus_valign('bottom')
            case ('down' | 'j', p) if p == len(self) - 1:
                self.focus_position = 0
                self.set_focus_valign('top')
            # TODO: figure-out the best semantics for vi key bindings
            case ('j', _):
                return super().keypress(size, 'down')
            case ('k', _):
                return super().keypress(size, 'up')
            # case ('h', _):
            #     return super().keypress(size, 'page up')
            # case ('l', _):
            #     return super().keypress(size, 'page down')
            case _:
                return super().keypress(size, key)
