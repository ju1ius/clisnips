"""
GRAMMAR
=======
documentation:  header param_list code
header:         TEXT*
param_list:     param_doc*
code:           CODE_FENCE TEXT CODE_FENCE
param_doc:      LEFT_BRACE param_id? RIGHT_BRACE type_hint? value_hint? TEXT*
param_id:       identifier | flag
identifier:     IDENTIFIER | INTEGER
flag:           FLAG
type_hint:      LEFT_PAREN IDENTIFIER RIGHT_PAREN
value_hint:     LEFT_BRACKET (value_list | value_range) RIGHT_BRACKET
value_list:     value (COMMA value)*
value_range:    DIGIT COLON digit (COLON digit)? (STAR digit)?
value:          STAR? (STRING | digit)
digit:          INTEGER | FLOAT
"""

from collections.abc import Iterable
from decimal import Decimal

from clisnips.exceptions import DocumentationParseError
from clisnips.syntax.llk_parser import LLkParser

from .lexer import Lexer, Tokens
from .nodes import CodeBlock, Documentation, Parameter, Value, ValueList, ValueRange


def _to_number(string: str) -> Decimal:
    return Decimal(string)


class Parser(LLkParser[Tokens]):
    def __init__(self, lexer: Lexer):
        super().__init__(lexer, Tokens.EOF, 2)
        self._auto_field_count = -1
        self._has_numeric_field = False
        self._ast = None

    def parse(self):
        self.reset()
        self._auto_field_count = -1
        self._has_numeric_field = False
        self._ast = Documentation()
        self._ast.header = self._text()
        for param in self._param_list():
            self._ast.parameters[param.name] = param
        for block in self._code():
            self._ast.code_blocks.append(block)
        return self._ast

    def _text(self) -> str:
        """
        TEXT*
        """
        text: list[str] = []
        while True:
            t = self._lookahead()
            if t.kind is Tokens.TEXT:
                self._consume()
                text.append(t.value)
            else:
                break
        return ''.join(text)

    def _param_list(self) -> Iterable[Parameter]:
        """
        param_doc*
        """
        while True:
            t = self._lookahead()
            if t.kind is Tokens.LEFT_BRACE:
                yield self._param_doc()
            else:
                break

    def _code(self) -> list[CodeBlock]:
        """
        CODEBLOCK*
        """
        code_blocks: list[CodeBlock] = []
        while self._lookahead_kind() is Tokens.CODE_FENCE:
            self._match(Tokens.CODE_FENCE)
            code = self._match(Tokens.TEXT).value
            try:
                block = CodeBlock(code)
            except SyntaxError as err:
                raise DocumentationParseError(f'Syntax error: {err}') from err
            except TypeError as err:
                raise DocumentationParseError(f'Type error: {err}') from err
            else:
                code_blocks.append(block)
            self._match(Tokens.CODE_FENCE)
        return code_blocks

    def _param_doc(self) -> Parameter:
        """
        LEFT_BRACE param_id RIGHT_BRACE
        type_hint? value_hint? TEXT*
        """
        self._match(Tokens.LEFT_BRACE)
        param = self._param_id()
        self._match(Tokens.RIGHT_BRACE)

        token = self._lookahead()
        if token.kind is Tokens.LEFT_PAREN:
            if param.type_hint == 'flag':
                raise DocumentationParseError('A flag cannot have a type hint.')
            param.type_hint = self._typehint()
            token = self._lookahead()

        if token.kind is Tokens.LEFT_BRACKET:
            if param.type_hint == 'flag':
                raise DocumentationParseError('A flag cannot have a value hint.')
            param.value_hint = self._valuehint()
            token = self._lookahead()

        if token.kind is Tokens.TEXT:
            param.text = self._text()

        return param

    def _param_id(self) -> Parameter:
        # no identifier, try automatic numbering
        if self._lookahead_kind() is Tokens.RIGHT_BRACE:
            if self._has_numeric_field:
                raise DocumentationParseError('Cannot switch from manual to automatic field numbering')
            self._auto_field_count += 1
            return Parameter(str(self._auto_field_count))

        token = self._match(Tokens.IDENTIFIER, Tokens.INTEGER, Tokens.FLAG)
        # it's a flag
        if token.kind is Tokens.FLAG:
            param = Parameter(token.value)
            param.type_hint = 'flag'
            return param

        # it's an integer, check that numbering is correct
        if token.kind is Tokens.INTEGER:
            if self._auto_field_count > -1:
                raise DocumentationParseError('Cannot switch from automatic to manual field numbering')
            self._has_numeric_field = True

        return Parameter(token.value)

    def _typehint(self) -> str:
        """
        LEFT_PAREN IDENTIFIER RIGHT_PAREN
        """
        self._match(Tokens.LEFT_PAREN)
        hint = self._match(Tokens.IDENTIFIER).value
        self._match(Tokens.RIGHT_PAREN)
        return hint

    def _valuehint(self) -> ValueRange | ValueList:
        """
        LEFT_BRACKET (value_list | value_range) RIGHT_BRACKET
        """
        self._match(Tokens.LEFT_BRACKET)
        token = self._lookahead()
        if token.kind in (Tokens.INTEGER, Tokens.FLOAT) and self._lookahead_kind(2) is Tokens.COLON:
            valuehint = self._value_range()
        else:
            valuehint = self._value_list()
        self._match(Tokens.RIGHT_BRACKET)
        return valuehint

    def _value_list(self) -> ValueList:
        """
        value (COMMA value)*
        """
        values: list[Value] = []
        default, count = 0, 0
        initial, _ = self._value()
        values.append(initial)
        while True:
            count += 1
            t = self._lookahead()
            if t.kind is Tokens.COMMA:
                self._consume()
                value, is_default = self._value()
                values.append(value)
                if is_default:
                    default = count
            else:
                break
        return ValueList(values, default)

    def _value(self) -> tuple[Value, bool]:
        """
        STAR? (STRING | digit)
        """
        is_default = False
        token = self._match(Tokens.DEFAULT_MARKER, Tokens.STRING, Tokens.INTEGER, Tokens.FLOAT)
        if token.kind is Tokens.DEFAULT_MARKER:
            is_default = True
            token = self._match(Tokens.STRING, Tokens.INTEGER, Tokens.FLOAT)
        if token.kind is Tokens.STRING:
            return token.value, is_default
        else:
            return _to_number(token.value), is_default

    def _value_range(self) -> ValueRange:
        """
        digit COLON digit (COLON digit)? (STAR digit)?
        """
        start = self._digit().value
        self._match(Tokens.COLON)
        end = self._digit().value
        step, default = None, None
        token = self._lookahead()
        if token.kind is Tokens.COLON:
            self._consume()
            step = self._digit().value
            token = self._lookahead()
        if token.kind is Tokens.DEFAULT_MARKER:
            self._consume()
            default = self._digit().value
        return ValueRange(
            _to_number(start),
            _to_number(end),
            _to_number(step) if step is not None else None,
            _to_number(default) if default is not None else None,
        )

    def _digit(self):
        return self._match(Tokens.INTEGER, Tokens.FLOAT)
