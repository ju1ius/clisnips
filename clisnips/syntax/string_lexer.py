import re
from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Generic

from .token import Kind, Token

EMPTY = ''
_RE_CACHE: dict[tuple[str, bool], re.Pattern[str]] = {}


class StringLexer(ABC, Generic[Kind]):
    """
    A simple String lexer
    """

    def __init__(self, text: str = ''):
        self.text = text
        self.length: int = 0
        self.pos: int = -1
        self.col: int = -1
        self.line: int = -1
        self.char: str = EMPTY
        self.newline_pending: bool = False
        if text:
            self.set_text(text)

    @abstractmethod
    def __iter__(self) -> Iterator[Token[Kind]]:
        ...

    def set_text(self, text: str):
        self.text = text
        self.length = len(self.text)
        self.reset()

    def reset(self):
        self.pos = -1
        self.col = -1
        self.line = 0
        self.char = EMPTY
        self.newline_pending = False

    def lookahead(self, n: int = 1, accumulate: bool = False) -> str:
        pos = self.pos + n
        if pos < self.length:
            if accumulate:
                return self.text[self.pos + 1 : pos + 1]
            return self.text[pos]
        if accumulate:
            return self.text[self.pos + 1 :]
        return EMPTY

    def lookbehind(self, n: int = 1, accumulate: bool = False) -> str:
        pos = self.pos - n
        if pos >= 0:
            if accumulate:
                return self.text[pos : self.pos]
            return self.text[pos]
        if accumulate:
            return self.text[: self.pos]
        return EMPTY

    def advance(self, n: int = 1) -> str:
        if self.newline_pending:
            self.line += 1
            self.col = -1
        if self.pos + n >= self.length:
            self.char = EMPTY
            self.pos = self.length
            return self.char
        if n == 1:
            self.pos += 1
            self.col += 1
            self.char = self.text[self.pos]
            # self.newline_pending = "\n" == self.char
            return self.char
        text = self.text
        old_pos = self.pos
        new_pos = old_pos + n
        # count newlines between:
        # old_pos (+1 since it should have been handled by self.newline_pending)
        # and new_pos (not -1 since we will set the last to be pending)
        line_count = text.count('\n', old_pos, new_pos + 1)
        # print text[old_pos:new_pos+1], line_count
        if line_count > 0:
            last_line_pos = text.rfind('\n', old_pos, new_pos + 1)
            # print last_line_pos
            self.line += line_count
            self.col = new_pos - last_line_pos
        else:
            self.col += n
        self.pos = new_pos
        self.char = text[new_pos]
        # self.newline_pending = "\n" == self.char
        return self.char

    def recede(self, n: int = 1) -> str:
        if self.pos - n < 0:
            self.char = EMPTY
            return self.char
        old_pos = self.pos
        text = self.text
        new_pos = self.pos - n
        # count newlines between:
        # new_pos and old_pos (not+1 since it has been handled by advance already)
        line_count = text.count('\n', new_pos, old_pos)
        # print old_pos, new_pos, line_count, text[new_pos:old_pos+1]
        if line_count > 0:
            self.line -= line_count
            first_line_pos = text.find('\n', new_pos, old_pos)
            self.col = old_pos - first_line_pos - 1
            if first_line_pos == new_pos:
                self.col += 1
        else:
            self.col -= n
        self.pos = new_pos
        self.char = text[new_pos]
        return self.char

    def read(self, n: int = 1) -> str:
        start_pos = self.pos
        la = self.advance(n)
        if la is EMPTY:
            return EMPTY
        return self.text[start_pos : self.pos + 1]

    def unread(self, n: int = 1) -> str:
        end_pos = self.pos
        la = self.recede(n)
        if la is EMPTY:
            return EMPTY
        return self.text[self.pos : end_pos + 1]

    def consume(self, string: str):
        self.advance(len(string))

    def unconsume(self, string: str):
        self.recede(len(string))

    def read_until(self, pattern: str | re.Pattern, negate: bool = True, accumulate: bool = True) -> str:
        """
        Consumes the input string until we find a match for pattern
        """
        if not isinstance(pattern, re.Pattern):
            cache_key: tuple[str, bool] = (pattern, negate)
            if cache_key not in _RE_CACHE:
                neg = '^' if negate else ''
                _RE_CACHE[cache_key] = re.compile(rf'[{neg}{pattern}]+')
            pattern = _RE_CACHE[cache_key]
        m = pattern.match(self.text, self.pos)
        if m:
            self.advance(m.end() - 1 - m.start())
            return m.group(0)
        return EMPTY
