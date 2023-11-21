import re

import urwid

from clisnips.tui.urwid_types import TextMarkup


def _next_word_position(text: str, start_position: int) -> int:
    matches = re.finditer(r'(\b\W+|$)', text, flags=re.UNICODE)
    positions = (m.start() for m in matches)
    return next(
        (p for p in positions if p > start_position),
        len(text),
    )


def _prev_word_position(text: str, start_position: int) -> int:
    matches = re.finditer(r'(\w+\b|^)', text, flags=re.UNICODE)
    positions = reversed([m.start() for m in matches])
    return next(
        (p for p in positions if p < start_position),
        0,
    )


def _next_line_position(text: str, start_position: int) -> int:
    pos = text.find('\n', start_position)
    return pos if pos > -1 else len(text) - 1


def _prev_line_position(text: str, start_position: int) -> int:
    pos = text.rfind('\n', 0, start_position)
    return pos + 1 if pos > -1 else 0


class EmacsEdit(urwid.Edit):
    def keypress(self, size, key: str):
        match key:
            case 'ctrl left':
                return super().keypress(size, 'home')
            case 'ctrl right':
                return super().keypress(size, 'end')
            case 'meta right' | 'meta f':
                # goto next word
                self.edit_pos = _next_word_position(self.edit_text, self.edit_pos)
                return None
            case 'meta left' | 'meta b':
                # goto previous word
                self.edit_pos = _prev_word_position(self.edit_text, self.edit_pos)
                return None
            case 'ctrl k':
                # delete to EOL
                start = self.edit_pos
                end = _next_line_position(self.edit_text, start)
                self.edit_text = self.edit_text[:start] + self.edit_text[end:]
                return None
            case 'ctrl u' | 'ctrl backspace':
                # delete to SOL
                end = self.edit_pos
                start = _prev_line_position(self.edit_text, end)
                self.edit_text = self.edit_text[:start] + self.edit_text[end:]
                self.edit_pos = start
                return None
            case 'ctrl d':
                # delete char under cursor
                return super().keypress(size, 'delete')
            case 'meta d' | 'meta backspace':
                # delete next word
                start = self.edit_pos
                end = _next_word_position(self.edit_text, start)
                self.edit_text = self.edit_text[:start] + self.edit_text[end:]
                return None
            case 'ctrl w':
                # delete previous word
                end = self.edit_pos
                start = _prev_word_position(self.edit_text, end)
                self.edit_text = self.edit_text[:start] + self.edit_text[end:]
                self.edit_pos = start
                return None
            case 'space':
                return super().keypress(size, ' ')
            case _:
                return super().keypress(size, key)


class SourceEdit(EmacsEdit):
    """
    Edit subclass that supports markup.
    This works by calling set_edit_markup from the change event
    as well as whenever markup changes while text does not.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._edit_attrs = []

    def set_edit_markup(self, markup: TextMarkup):
        """
        Call this when markup changes but the underlying text does not.
        You should arrange for this to be called from the 'change' signal.
        """
        if markup:
            self._edit_text, self._edit_attrs = urwid.decompose_tagmarkup(markup)
        else:
            self._edit_text, self._edit_attrs = '', []
        # This is redundant when we're called off the 'change' signal.
        # I'm assuming this is cheap, making that ok.
        self._invalidate()

    def get_text(self):
        return self._caption + self._edit_text, self._attrib + self._edit_attrs
