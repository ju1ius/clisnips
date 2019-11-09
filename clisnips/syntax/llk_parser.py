from clisnips.exceptions import ParsingError


class LLkParser(object):

    def __init__(self, lexer, k=2):
        self._K = k
        self.lexer = lexer
        self.token_stream = None
        self.position = 0
        self._buffer = []

    def reset(self):
        self.lexer.reset()
        self.token_stream = iter(self.lexer)
        self.position = 0
        self._buffer = [None for i in range(self._K)]
        for i in range(self._K):
            self._consume()

    def _match(self, *types):
        token = self._ensure(*types)
        self._consume()
        return token

    def _ensure(self, *types):
        token = self._lookahead()
        if token.type not in types:
            self._unexpected_token(token, *types)
        return token

    def _consume(self):
        try:
            token = next(self.token_stream)
        except StopIteration:
            token = None
        self._buffer[self.position] = token
        self.position = (self.position + 1) % self._K

    def _consume_until(self, types):
        if isinstance(types, (tuple, list)):
            while self._lookahead_type() not in types:
                self._consume()
        else:
            while self._lookahead_type() != types:
                self._consume()

    def _current(self):
        return self._buffer[self.position]

    def _lookahead(self, offset=1):
        return self._buffer[(self.position + offset - 1) % self._K]

    def _lookahead_type(self, offset=1):
        return self._lookahead(offset).type

    def _unexpected_token(self, token, *expected):
        expected = ', '.join(t.name for t in expected)
        raise ParsingError(f'Unexpected token: {token.name} (expected {expected})')
