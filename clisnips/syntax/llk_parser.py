from typing import Generic, Never

from clisnips.exceptions import ParseError
from clisnips.syntax.string_lexer import StringLexer
from clisnips.syntax.token import Kind, Token


class LLkParser(Generic[Kind]):
    def __init__(self, lexer: StringLexer[Kind], eof: Kind, k: int = 2):
        self._K = k
        self._eof_marker = Token(eof, 0, 0)
        self.lexer = lexer
        self.token_stream = iter(self.lexer)
        self.position = 0
        self._buffer = [self._eof_marker for _ in range(self._K)]

    def reset(self):
        self.lexer.reset()
        self.token_stream = iter(self.lexer)
        self.position = 0
        self._buffer = [self._eof_marker for _ in range(self._K)]
        for _ in range(self._K):
            self._consume()

    def _match(self, *kinds: Kind):
        token = self._ensure(*kinds)
        self._consume()
        return token

    def _ensure(self, *kinds: Kind) -> Token[Kind]:
        token = self._lookahead()
        if token.kind not in kinds:
            self._unexpected_token(token, *kinds)
        return token

    def _consume(self):
        try:
            token = next(self.token_stream)
        except StopIteration:
            token = self._eof_marker
        self._buffer[self.position] = token
        self.position = (self.position + 1) % self._K

    def _consume_until(self, *kinds: Kind):
        while self._lookahead_kind() not in kinds:
            self._consume()

    def _current(self) -> Token[Kind] | None:
        return self._buffer[self.position]

    def _lookahead(self, offset: int = 1) -> Token[Kind]:
        return self._buffer[(self.position + offset - 1) % self._K]

    def _lookahead_kind(self, offset: int = 1) -> Kind:
        return self._lookahead(offset).kind

    def _unexpected_token(self, token: Token[Kind], *expected: Kind) -> Never:
        exp = ', '.join(t.name for t in expected)
        raise ParseError(
            f'Unexpected token: {token.name}'
            f' on line {token.start_line + 1}, column {token.start_col + 1}'
            f' (expected {exp})'
        )
