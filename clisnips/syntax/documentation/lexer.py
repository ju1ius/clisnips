import enum
import re
from collections import deque
from typing import Match, Optional

from clisnips.syntax.string_lexer import EMPTY, StringLexer
from clisnips.syntax.token import Token


class Tokens(enum.IntEnum):
    EOF = enum.auto()
    TEXT = enum.auto()
    IDENTIFIER = enum.auto()
    FLAG = enum.auto()
    INTEGER = enum.auto()
    FLOAT = enum.auto()
    STRING = enum.auto()
    CODE_FENCE = enum.auto()
    LEFT_BRACE = enum.auto()
    RIGHT_BRACE = enum.auto()
    LEFT_BRACKET = enum.auto()
    RIGHT_BRACKET = enum.auto()
    LEFT_PAREN = enum.auto()
    RIGHT_PAREN = enum.auto()
    COMMA = enum.auto()
    COLON = enum.auto()
    DEFAULT_MARKER = enum.auto()


WSP_CHARS = '\t\f\x20'
WSP_RX = re.compile(r'[\t\f ]*')

PARAM_START_RX = re.compile(r'^[\t\f ]*(?={)', re.MULTILINE)
CODE_BLOCK_START_RX = re.compile(r'^[\t\f ]*(?=```$)', re.MULTILINE)
FREE_TEXT_BOUNDS_RX = re.compile(
    r'''
        ^               # start of string or line
        [\x20\t\f]*     # any whitespace except newline
        (?=             # followed by
            {           # parameter start char
            |           # or
            ```$        # code block start marker
        )
    ''',
    re.MULTILINE | re.X
)

IDENTIFIER_RX = re.compile(r'[_a-zA-Z][_a-zA-Z0-9]*')
FLAG_RX = re.compile(r'--?[a-zA-Z0-9][\w-]*')
PARAM_RX = re.compile(r'(\d+)|({ident})'.format(ident=IDENTIFIER_RX.pattern))
INTEGER_RX = re.compile(r'\d+')
FLOAT_RX = re.compile(r'\d*\.\d+')
TYPE_HINT_RX = re.compile(r'\(\s*({ident})\s*\)'.format(ident=IDENTIFIER_RX.pattern))
DIGIT_RX = re.compile(r'-?(?:({float})|({int}))'.format(float=FLOAT_RX.pattern, int=INTEGER_RX.pattern))
STRING_RX = re.compile(r'''(["']) ( (?: \\. | (?!\1) . )* ) \1''', re.X)
DQ_STR_RX = re.compile(r'"(?:\\.|[^"])*"')
SQ_STR_RX = re.compile(r"'(?:\\.|[^'])*'")
TQ_STR_RX = re.compile(r'(\'\'\'|""")(?:\\.|[^\\])*\1')


class Lexer(StringLexer):
    """
    A stateful lexer
    """

    def __init__(self, text):
        super().__init__(text)
        self.state = self.free_text_state
        self.token_queue = deque()

    def __iter__(self):
        self.token_queue = deque()
        while True:
            if not self.state():
                yield Token(Tokens.EOF, self.line, self.col)
                break
            while self.token_queue:
                token = self.token_queue.popleft()
                yield token

    def init_token(self, type: Tokens, value: str = EMPTY) -> Token:
        token = Token(type, self.line, self.col, value)
        token.start_pos = self.pos
        return token

    def finalize_token(self, token: Token, line: Optional[int] = None, col: Optional[int] = None,
                       pos: Optional[int] = None, value: Optional[str] = None):
        if value is not None:
            token.value = value
        token.end_pos = pos if pos is not None else self.pos
        token.end_line = line if line is not None else self.line
        token.end_col = col if col is not None else self.col
        return token

    def free_text_state(self) -> bool:
        char = self.advance()
        if char is EMPTY:
            return False
        if char == '{':
            token = self.init_token(Tokens.LEFT_BRACE, '{')
            self.finalize_token(token)
            self.token_queue.append(token)
            self.state = self.param_state
            return True
        if char == '`':
            if self.lookahead(2, True) == '``':
                token = self.init_token(Tokens.CODE_FENCE, '```')
                self.advance(2)
                self.finalize_token(token)
                self.token_queue.append(token)
                self.state = self.code_block_state
                return True
        token = self.init_token(Tokens.TEXT)
        text = self._consume_free_text()
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
                token = self.init_token(Tokens.RIGHT_BRACE, '}')
                self.finalize_token(token)
                self.token_queue.append(token)
                self.state = self.after_param_state
                break
            if char.isalnum() or char == '_':
                token = self._handle_param_identifier()
                if not token:
                    self.state = self.free_text_state
                    break
                self.token_queue.append(token)
            elif char == '-':
                token = self._handle_flag()
                if not token:
                    self.state = self.free_text_state
                    break
                self.token_queue.append(token)
            else:
                self.state = self.free_text_state
                break
        return True

    def after_param_state(self) -> bool:
        char = self._skip_whitespace()
        if char is EMPTY:
            return False
        if char == '(':
            token = self.init_token(Tokens.LEFT_PAREN, '(')
            self.token_queue.append(token)
            self.state = self.type_hint_state
            return True
        if char == '[':
            token = self.init_token(Tokens.LEFT_BRACKET, '[')
            self.token_queue.append(token)
            self.state = self.value_hint_state
            return True
        self.recede()
        self.state = self.free_text_state
        return True

    def type_hint_state(self) -> bool:
        while True:
            char = self._skip_whitespace()
            if char is EMPTY:
                return False
            if char == ')':
                token = self.init_token(Tokens.RIGHT_PAREN, ')')
                self.token_queue.append(token)
                self.state = self.after_param_state
                break
            m = IDENTIFIER_RX.match(self.text, self.pos)
            if not m:
                self.recede()
                self.state = self.free_text_state
                break
            token = self.init_token(Tokens.IDENTIFIER, m.group(0))
            self._consume_match(m)
            self.finalize_token(token)
            self.token_queue.append(token)
        return True

    def value_hint_state(self) -> bool:
        while True:
            token = None
            char = self._skip_whitespace()
            if char is EMPTY:
                return False
            if char == ']':
                token = self.init_token(Tokens.RIGHT_BRACKET, ']')
                self.finalize_token(token)
                self.token_queue.append(token)
                self.state = self.free_text_state
                break
            elif char in ('"', "'"):
                token = self._handle_quoted_string()
                if not token:
                    self.state = self.free_text_state
                    break
                self.token_queue.append(token)
            elif char == ',':
                token = self.init_token(Tokens.COMMA, ',')
                self.finalize_token(token)
                self.token_queue.append(token)
            elif char == ':':
                token = self.init_token(Tokens.COLON, ':')
                self.token_queue.append(token)
            elif char == '=':
                if self.lookahead() == '>':
                    token = self.init_token(Tokens.DEFAULT_MARKER, '=>')
                    self.advance()
                    self.finalize_token(token)
                    self.token_queue.append(token)
                else:
                    self.recede()
                    self.state = self.free_text_state
                    break
            else:
                token = self._handle_digit()
                if not token:
                    self.recede()
                    self.state = self.free_text_state
                    break
                self.token_queue.append(token)
        return True

    def code_block_state(self) -> bool:
        code = self.init_token(Tokens.TEXT, '')
        while True:
            code.value += self.read_until(r'"\'`')
            char = self.advance()
            if not char:
                self.finalize_token(code)
                self.token_queue.append(code)
                return False
            if char == '"':
                if self.lookahead(2, True) == '""':
                    m = TQ_STR_RX.match(self.text, self.pos)
                    if m:
                        code.value += m.group(0)
                        self._consume_match(m)
                    else:
                        code.value += char
                    continue
                m = DQ_STR_RX.match(self.text, self.pos)
                if m:
                    code.value += m.group(0)
                    self._consume_match(m)
                else:
                    code.value += char
            elif char == "'":
                if self.lookahead(2, True) == "''":
                    m = TQ_STR_RX.match(self.text, self.pos)
                    if m:
                        code.value += m.group(0)
                        self._consume_match(m)
                    else:
                        code.value += char
                    continue
                m = SQ_STR_RX.match(self.text, self.pos)
                if m:
                    code.value += m.group(0)
                    self._consume_match(m)
                else:
                    code.value += char
            elif char == '`':
                if self.lookahead(2, True) == '``':
                    self.finalize_token(code)
                    self.token_queue.append(code)
                    token = self.init_token(Tokens.CODE_FENCE, '```')
                    self.advance(2)
                    self.finalize_token(token)
                    self.token_queue.append(token)
                    self.state = self.free_text_state
                    break
                code.value += char
        return True

    def _handle_param_identifier(self) -> Optional[Token]:
        m = PARAM_RX.match(self.text, self.pos)
        if not m:
            return None
        if m.group(1):
            _type = Tokens.INTEGER
        elif m.group(2):
            _type = Tokens.IDENTIFIER
        token = self.init_token(_type, m.group(0))
        self._consume_match(m)
        return self.finalize_token(token)

    def _handle_flag(self) -> Optional[Token]:
        m = FLAG_RX.match(self.text, self.pos)
        if not m:
            return None
        token = self.init_token(Tokens.FLAG, m.group(0))
        self._consume_match(m)
        return self.finalize_token(token)

    def _handle_quoted_string(self) -> Optional[Token]:
        m = STRING_RX.match(self.text, self.pos)
        if not m:
            return None
        token = self.init_token(Tokens.STRING, m.group(2))
        self._consume_match(m)
        return self.finalize_token(token)

    def _handle_digit(self) -> Optional[Token]:
        m = DIGIT_RX.match(self.text, self.pos)
        if not m:
            return None
        if m.group(1):
            _type = Tokens.FLOAT
        elif m.group(2):
            _type = Tokens.INTEGER
        token = self.init_token(_type, m.group(0))
        self._consume_match(m)
        return self.finalize_token(token)

    def _consume_free_text(self) -> str:
        m = FREE_TEXT_BOUNDS_RX.search(self.text, self.pos)
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

    def _consume_match(self, match: Match, group: int | str = 0) -> str:
        if not match:
            return EMPTY
        self.advance(match.end(group) - 1 - match.start(group))
        return match.group(group)
