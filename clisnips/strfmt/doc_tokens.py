from typing import Dict, Union

(
    T_EOF,
    T_TEXT,
    T_IDENTIFIER,
    T_FLAG,
    T_INTEGER, T_FLOAT,
    T_STRING,
    T_PARAM,
    T_TYPEHINT,
    T_CODEMARK,
    T_LBRACE, T_RBRACE,
    T_LBRACK, T_RBRACK,
    T_LPAREN, T_RPAREN,
    T_COMMA,
    T_COLON,
    T_DEFAULT_MARKER
) = range(19)

__TOKEN_NAMES: Dict[int, str] = {}

for k, v in dict(vars()).items():
    if k.startswith('T_'):
        __TOKEN_NAMES[v] = k
# noinspection PyUnboundLocalVariable
del k, v


def token_name(token_type: Union[int, 'Token']):
    """Returns the token name given its type"""
    if isinstance(token_type, Token):
        token_type = token_type.type
    return __TOKEN_NAMES[token_type]


class Token:

    __slots__ = (
        'type', 'value',
        'startline', 'startcol', 'endline', 'endcol',
        'startpos', 'endpos'
    )

    @property
    def name(self) -> str:
        return token_name(self.type)

    def __init__(self, type: int, startline: int, startcol: int, value: str = ''):
        self.type = type
        self.startline = startline
        self.startcol = startcol
        self.value = value
        self.endline = startline
        self.endcol = startcol
        self.startpos = self.endpos = -1

    def __str__(self):
        return f'{self.name} {self.value!r} on line {self.startline}, column {self.startcol}'

    def __repr__(self):
        pos = ''
        if self.startpos >= 0:
            pos = f' {self.startpos}->{self.endpos}'
        return (f'<Token {self.name} @{pos} '
                f'({self.startline},{self.startcol})->({self.endline},{self.endcol}) : {self.value!r}>')
