import operator
import re

import urwid


def _next_word_position(text: str, start_position: int, backward=False):
    if backward:
        match_iterator = re.finditer(r'(\w+\b|^)', text, flags=re.UNICODE)
        match_positions = reversed([m.start() for m in match_iterator])
        op = operator.lt
    else:
        match_iterator = re.finditer(r'(\b\W+|$)', text, flags=re.UNICODE)
        match_positions = (m.start() for m in match_iterator)
        op = operator.gt
    for pos in match_positions:
        if op(pos, start_position):
            return pos


class EmacsEdit(urwid.Edit):

    def keypress(self, size, key):
        if key == 'ctrl left':
            return super().keypress(size, 'home')
        if key == 'ctrl right':
            return super().keypress(size, 'end')
        if key in ('alt right', 'alt f'):
            # goto next word
            self.set_edit_pos(_next_word_position(self.edit_text, self.edit_pos))
            return None
        if key in ('alt left', 'alt b'):
            # goto previous word
            self.set_edit_pos(_next_word_position(self.edit_text, self.edit_pos, backward=True))
            return None
        if key == 'ctrl k':
            # delete to EOL
            self.edit_text = self.edit_text[:self.edit_pos]
            return None
        if key in ('ctrl u', 'ctrl backspace'):
            # delete to SOL
            self.edit_text = ''
            return None
        if key == 'ctrl d':
            # delete char under cursor
            return super().keypress(size, 'delete')
        if key == 'ctrl w':
            # delete next word
            end_pos = self.edit_pos
            start_pos = _next_word_position(self.edit_text, end_pos, backward=True)
            if start_pos is not None:
                self.set_edit_text(self.edit_text[:start_pos] + self.edit_text[end_pos:])
            return None
        if key in ('alt d', 'alt backspace'):
            # delete previous word
            end_pos = self.edit_pos
            start_pos = _next_word_position(self.edit_text, end_pos)
            if start_pos is not None:
                self.set_edit_text(self.edit_text[:start_pos] + self.edit_text[end_pos:])
            return None
        if key == 'space':
            return super().keypress(size, ' ')
        return super().keypress(size, key)
