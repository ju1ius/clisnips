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
    T_STAR
) = range(19)

__TOKEN_NAMES = {}

for k, v in dict(vars()).iteritems():
    if k.startswith('T_'):
        __TOKEN_NAMES[v] = k
del k, v


def token_name(token_type):
    """Returns the token name given its type"""
    if isinstance(token_type, Token):
        token_type = token_type.type
    return __TOKEN_NAMES[token_type]


class Token(object):

    __slots__ = (
        'type', 'name', 'value',
        'startline', 'startcol', 'endline', 'endcol',
        'startpos', 'endpos'
    )

    def __init__(self, type, startline, startcol, value=''):
        self.type = type
        self.name = token_name(type)
        self.startline = startline
        self.startcol = startcol
        self.value = value
        self.endline = startline
        self.endcol = startcol
        self.startpos = self.endpos = None

    def __str__(self):
        return ('{s.name} {s.value!r} on line {s.startline}, '
                'column {s.startcol}').format(s=self)

    def __repr__(self):
        pos = ''
        if self.startpos is not None:
            pos = '%s->%s' % (self.startpos, self.endpos)
        return ('<Token {s.name} @ {pos} '
                '({s.startline},{s.startcol})->({s.endline},'
                '{s.endcol}) : {s.value!r}>').format(s=self, pos=pos)
