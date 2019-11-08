import re
from collections import deque
from typing import Match, Optional, Pattern, Tuple

from .doc_tokens import *

_RE_CACHE: Dict[Tuple[str, bool], Pattern[str]] = {}

WSP_CHARS = '\t\f\x20'
WSP_RX = re.compile(r'[\t\f ]*')

PARAM_START_RX = re.compile(r'^[\t\f ]*(?={)', re.MULTILINE)
CODEBLOCK_START_RX = re.compile(r'^[\t\f ]*(?=```$)', re.MULTILINE)
FREETEXT_BOUNDS_RX = re.compile(
    r'''
        ^               # start of string or line
        [\x20\t\f]*     # any whitespace except newline
        (?=             # followed by
            {           # parameter start char
            |           # or
            ```$        # codeblock start marker
        )
    ''',
    re.MULTILINE | re.X
)

IDENT_RX = re.compile(r'[_a-zA-Z][_a-zA-Z0-9]*')
FLAG_RX = re.compile(r'--?[a-zA-Z0-9][\w-]*')
PARAM_RX = re.compile(r'(\d+)|({ident})'.format(ident=IDENT_RX.pattern))
INTEGER_RX = re.compile(r'\d+')
FLOAT_RX = re.compile(r'\d*\.\d+')
TYPEHINT_RX = re.compile(r'\(\s*({ident})\s*\)'.format(ident=IDENT_RX.pattern))
DIGIT_RX = re.compile(r'-?(?:({float})|({int}))'.format(float=FLOAT_RX.pattern, int=INTEGER_RX.pattern))
STRING_RX = re.compile(r'''(["']) ( (?: \\. | (?!\1) . )* ) \1''', re.X)
DSTR_RX = re.compile(r'"(?:\\.|[^"])*"')
SSTR_RX = re.compile(r"'(?:\\.|[^'])*'")
TSTR_RX = re.compile(r'(\'\'\'|""")(?:\\.|[^\\])*\1')

EMPTY = ''


class StringLexer(object):
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
                return self.text[self.pos + 1:pos + 1]
            return self.text[pos]
        if accumulate:
            return self.text[self.pos + 1:]
        return EMPTY

    def lookbehind(self, n: int = 1, accumulate: bool = False) -> str:
        pos = self.pos - n
        if pos >= 0:
            if accumulate:
                return self.text[pos:self.pos]
            return self.text[pos]
        if accumulate:
            return self.text[:self.pos]
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
        # oldpos (+1 since it should have been handled by self.newline_pending)
        # and newpos (not -1 since we will set the last to be pending)
        line_count = text.count("\n", old_pos, new_pos + 1)
        # print text[old_pos:new_pos+1], line_count
        if line_count > 0:
            last_line_pos = text.rfind("\n", old_pos, new_pos + 1)
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
        # new_pos and old_pos (not+1 since it has been handled by advance
        # already)
        line_count = text.count("\n", new_pos, old_pos)
        # print old_pos, new_pos, line_count, text[new_pos:old_pos+1]
        if line_count > 0:
            self.line -= line_count
            first_line_pos = text.find("\n", new_pos, old_pos)
            self.col = old_pos - first_line_pos - 1
            if first_line_pos == new_pos:
                self.col += 1
        else:
            self.col -= n
        self.pos = new_pos
        self.char = text[new_pos]
        return self.char

    def read(self, n: int = 1) -> str:
        startpos = self.pos
        la = self.advance(n)
        if la is EMPTY:
            return EMPTY
        return self.text[startpos:self.pos + 1]

    def unread(self, n: int = 1) -> str:
        endpos = self.pos
        la = self.recede(n)
        if la is EMPTY:
            return EMPTY
        return self.text[self.pos:endpos + 1]

    def consume(self, string: str):
        self.advance(len(string))

    def unconsume(self, string: str):
        self.recede(len(string))

    def read_until(self, pattern: Union[str, Pattern], negate: bool = True, accumulate: bool = True) -> str:
        """
        Consumes the input string until we find a match for pattern
        """
        if not isinstance(pattern, Pattern):
            cache_key: Tuple[str, bool] = (pattern, negate)
            if cache_key not in _RE_CACHE:
                neg = '^' if negate else ''
                _RE_CACHE[cache_key] = re.compile(fr'[{neg}{pattern}]+')
            pattern = _RE_CACHE[cache_key]
        m = pattern.match(self.text, self.pos)
        if m:
            self.advance(m.end() - 1 - m.start())
            return m.group(0)
        return EMPTY


class Lexer(StringLexer):
    """
    A stateful lexer
    """

    def __init__(self, text):
        super().__init__(text)
        self.state = self.freetext_state
        self.token_queue = deque()

    def __iter__(self):
        self.token_queue = deque()
        while True:
            if not self.state():
                yield Token(T_EOF, self.line, self.col)
                break
            while self.token_queue:
                token = self.token_queue.popleft()
                yield token

    def init_token(self, type: int, value: str = EMPTY) -> Token:
        token = Token(type, self.line, self.col, value)
        token.startpos = self.pos
        return token

    def finalize_token(self, token: Token, line: Optional[int] = None, col: Optional[int] = None,
                       pos: Optional[int] = None, value: Optional[str] = None):
        if value is not None:
            token.value = value
        token.endpos = pos if pos is not None else self.pos
        token.endline = line if line is not None else self.line
        token.endcol = col if col is not None else self.col
        return token

    def freetext_state(self) -> bool:
        char = self.advance()
        if char is EMPTY:
            return False
        if char == '{':
            token = self.init_token(T_LBRACE, '{')
            self.finalize_token(token)
            self.token_queue.append(token)
            self.state = self.param_state
            return True
        if char == '`':
            if self.lookahead(2, True) == '``':
                token = self.init_token(T_CODEMARK, '```')
                self.advance(2)
                self.finalize_token(token)
                self.token_queue.append(token)
                self.state = self.codeblock_state
                return True
        token = self.init_token(T_TEXT)
        text = self._consume_freetext()
        if not text:
            text = self.read_until('$')
        self.finalize_token(token, value=text)
        self.token_queue.append(token)
        return True

    def param_state(self) -> bool:
        while True:
            token = None
            char = self._skip_whitespace()
            if char == '}':
                token = self.init_token(T_RBRACE, '}')
                self.finalize_token(token)
                self.token_queue.append(token)
                self.state = self.after_param_state
                break
            if char.isalnum() or char == '_':
                token = self._handle_param_identifier()
                if not token:
                    self.state = self.freetext_state
                    break
                self.token_queue.append(token)
            elif char == '-':
                token = self._handle_flag()
                if not token:
                    self.state = self.freetext_state
                    break
                self.token_queue.append(token)
            else:
                self.state = self.freetext_state
                break
        return True

    def after_param_state(self) -> bool:
        char = self._skip_whitespace()
        if char is EMPTY:
            return False
        if char == '(':
            token = self.init_token(T_LPAREN, '(')
            self.token_queue.append(token)
            self.state = self.typehint_state
            return True
        if char == '[':
            token = self.init_token(T_LBRACK, '[')
            self.token_queue.append(token)
            self.state = self.valuehint_state
            return True
        self.recede()
        self.state = self.freetext_state
        return True

    def typehint_state(self) -> bool:
        while True:
            char = self._skip_whitespace()
            if char is EMPTY:
                return False
            if char == ')':
                token = self.init_token(T_RPAREN, ')')
                self.token_queue.append(token)
                self.state = self.after_param_state
                break
            m = IDENT_RX.match(self.text, self.pos)
            if not m:
                self.recede()
                self.state = self.freetext_state
                break
            token = self.init_token(T_IDENTIFIER, m.group(0))
            self._consume_match(m)
            self.finalize_token(token)
            self.token_queue.append(token)
        return True

    def valuehint_state(self) -> bool:
        while True:
            token = None
            char = self._skip_whitespace()
            if char is EMPTY:
                return False
            if char == ']':
                token = self.init_token(T_RBRACK, ']')
                self.finalize_token(token)
                self.token_queue.append(token)
                self.state = self.freetext_state
                break
            elif char in ('"', "'"):
                token = self._handle_quoted_string()
                if not token:
                    self.state = self.freetext_state
                    break
                self.token_queue.append(token)
            elif char == ',':
                token = self.init_token(T_COMMA, ',')
                self.finalize_token(token)
                self.token_queue.append(token)
            elif char == ':':
                token = self.init_token(T_COLON, ':')
                self.token_queue.append(token)
            elif char == '=':
                if self.lookahead() == '>':
                    token = self.init_token(T_DEFAULT_MARKER, '=>')
                    self.advance()
                    self.finalize_token(token)
                    self.token_queue.append(token)
                else:
                    self.recede()
                    self.state = self.freetext_state
                    break
            else:
                token = self._handle_digit()
                if not token:
                    self.recede()
                    self.state = self.freetext_state
                    break
                self.token_queue.append(token)
        return True

    def codeblock_state(self) -> bool:
        code = self.init_token(T_TEXT, '')
        while True:
            code.value += self.read_until(r'"\'`')
            char = self.advance()
            if not char:
                self.finalize_token(code)
                self.token_queue.append(code)
                return False
            if char == '"':
                if self.lookahead(2, True) == '""':
                    m = TSTR_RX.match(self.text, self.pos)
                    if m:
                        code.value += m.group(0)
                        self._consume_match(m)
                    else:
                        code.value += char
                    continue
                m = DSTR_RX.match(self.text, self.pos)
                if m:
                    code.value += m.group(0)
                    self._consume_match(m)
                else:
                    code.value += char
            elif char == "'":
                if self.lookahead(2, True) == "''":
                    m = TSTR_RX.match(self.text, self.pos)
                    if m:
                        code.value += m.group(0)
                        self._consume_match(m)
                    else:
                        code.value += char
                    continue
                m = SSTR_RX.match(self.text, self.pos)
                if m:
                    code.value += m.group(0)
                    self._consume_match(m)
                else:
                    code.value += char
            elif char == '`':
                if self.lookahead(2, True) == '``':
                    self.finalize_token(code)
                    self.token_queue.append(code)
                    token = self.init_token(T_CODEMARK, '```')
                    self.advance(2)
                    self.finalize_token(token)
                    self.token_queue.append(token)
                    self.state = self.freetext_state
                    break
                code.value += char
        return True

    def _handle_param_identifier(self) -> Optional[Token]:
        m = PARAM_RX.match(self.text, self.pos)
        if not m:
            return None
        if m.group(1):
            _type = T_INTEGER
        elif m.group(2):
            _type = T_IDENTIFIER
        token = self.init_token(_type, m.group(0))
        self._consume_match(m)
        return self.finalize_token(token)

    def _handle_flag(self) -> Optional[Token]:
        m = FLAG_RX.match(self.text, self.pos)
        if not m:
            return None
        token = self.init_token(T_FLAG, m.group(0))
        self._consume_match(m)
        return self.finalize_token(token)

    def _handle_quoted_string(self) -> Optional[Token]:
        m = STRING_RX.match(self.text, self.pos)
        if not m:
            return None
        token = self.init_token(T_STRING, m.group(2))
        self._consume_match(m)
        return self.finalize_token(token)

    def _handle_digit(self) -> Optional[Token]:
        m = DIGIT_RX.match(self.text, self.pos)
        if not m:
            return None
        if m.group(1):
            _type = T_FLOAT
        elif m.group(2):
            _type = T_INTEGER
        token = self.init_token(_type, m.group(0))
        self._consume_match(m)
        return self.finalize_token(token)

    def _consume_freetext(self) -> str:
        m = FREETEXT_BOUNDS_RX.search(self.text, self.pos)
        if not m:
            return EMPTY
        end = m.end()
        text = self.text[self.pos:end]
        self.advance(end - self.pos - 1)
        return text

    def _skip_whitespace(self) -> str:
        char = self.advance()
        if char in WSP_CHARS:
            self.read_until(WSP_RX)
            char = self.advance()
        return char

    def _consume_match(self, match: Match, group: Union[int, str] = 0) -> str:
        if not match:
            return EMPTY
        self.advance(match.end(group) - 1 - match.start(group))
        return match.group(group)
