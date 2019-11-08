import enum


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


class Token:

    __slots__ = (
        'type', 'value',
        'start_line', 'start_col', 'end_line', 'end_col',
        'start_pos', 'end_pos'
    )

    @property
    def name(self) -> str:
        return self.type.name

    def __init__(self, type: Tokens, start_line: int, start_col: int, value: str = ''):
        self.type = type
        self.start_line = start_line
        self.start_col = start_col
        self.value = value
        self.end_line = start_line
        self.end_col = start_col
        self.start_pos = self.end_pos = -1

    def __str__(self):
        return f'{self.type.name} {self.value!r} on line {self.start_line}, column {self.start_col}'

    def __repr__(self):
        pos = ''
        if self.start_pos >= 0:
            pos = f' {self.start_pos}->{self.end_pos}'
        return (f'<Token {self.type.name} @{pos} '
                f'({self.start_line},{self.start_col})->({self.end_line},{self.end_col}) : {self.value!r}>')
