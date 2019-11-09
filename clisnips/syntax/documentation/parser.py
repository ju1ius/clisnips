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
from clisnips.exceptions import ParsingError
from clisnips.syntax.documentation.lexer import Tokens
from clisnips.syntax.documentation.nodes import *
from clisnips.syntax.llk_parser import LLkParser


def _to_number(string):
    if '.' in string:
        return float(string)
    return int(string)


class Parser(LLkParser):

    def __init__(self, lexer):
        super().__init__(lexer, 2)
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

    def _text(self):
        """
        TEXT*
        """
        text = []
        while True:
            t = self._lookahead()
            if t.type is Tokens.TEXT:
                self._consume()
                text.append(t.value)
            else:
                break
        return ''.join(text)

    def _param_list(self):
        """
        param_doc*
        """
        while True:
            t = self._lookahead()
            if t.type is Tokens.LEFT_BRACE:
                yield self._param_doc()
            else:
                break

    def _code(self):
        """
        CODEBLOCK*
        """
        code_blocks = []
        while self._lookahead_type() is Tokens.CODE_FENCE:
            self._match(Tokens.CODE_FENCE)
            code = self._match(Tokens.TEXT).value
            try:
                block = CodeBlock(code)
            except SyntaxError as err:
                raise ParsingError(f'Syntax error in code block: {code!r} \n{err!s}')
            except TypeError as err:
                raise ParsingError(f'Null bytes in code block: {code!r}')
            else:
                code_blocks.append(block)
            self._match(Tokens.CODE_FENCE)
        return code_blocks

    def _param_doc(self):
        """
        LEFT_BRACE param_id RIGHT_BRACE
        type_hint? value_hint? TEXT*
        """
        typehint, valuehint, text = None, None, None
        self._match(Tokens.LEFT_BRACE)
        param = self._param_id()
        self._match(Tokens.RIGHT_BRACE)

        token = self._lookahead()
        if token.type is Tokens.LEFT_PAREN:
            if param.type_hint == 'flag':
                raise ParsingError('A flag cannot have a type hint.')
            param.type_hint = self._typehint()
            token = self._lookahead()
        if token.type is Tokens.LEFT_BRACKET:
            if param.type_hint == 'flag':
                raise ParsingError('A flag cannot have a value hint.')
            param.value_hint = self._valuehint()
            token = self._lookahead()
        if token.type is Tokens.TEXT:
            param.text = self._text()
        return param

    def _param_id(self):
        # no identifier, try automatic numbering
        if self._lookahead_type() is Tokens.RIGHT_BRACE:
            if self._has_numeric_field:
                raise ParsingError('Cannot switch from manual to automatic field numbering')
            self._auto_field_count += 1
            return Parameter(str(self._auto_field_count))
        token = self._match(Tokens.IDENTIFIER, Tokens.INTEGER, Tokens.FLAG)
        # it's a flag
        if token.type is Tokens.FLAG:
            param = Parameter(token.value)
            param.type_hint = 'flag'
            return param
        # it's an integer, check that numbering is correct
        if token.type is Tokens.INTEGER:
            if self._auto_field_count > -1:
                raise ParsingError('Cannot switch from automatic to manual field numbering')
            self._has_numeric_field = True
        return Parameter(token.value)

    def _typehint(self):
        """
        LEFT_PAREN IDENTIFIER RIGHT_PAREN
        """
        self._match(Tokens.LEFT_PAREN)
        hint = self._match(Tokens.IDENTIFIER).value
        self._match(Tokens.RIGHT_PAREN)
        return hint 

    def _valuehint(self):
        """
        LEFT_BRACKET (value_list | value_range) RIGHT_BRACKET
        """
        self._match(Tokens.LEFT_BRACKET)
        token = self._lookahead()
        if (
            token.type in (Tokens.INTEGER, Tokens.FLOAT)
            and self._lookahead_type(2) is Tokens.COLON
        ):
            valuehint = self._value_range()
        else:
            valuehint = self._value_list()
        self._match(Tokens.RIGHT_BRACKET)
        return valuehint

    def _value_list(self):
        """
        value (COMMA value)*
        """
        values = []
        default, count = 0, 0
        initial = self._value()
        values.append(initial['value'])
        while True:
            count += 1
            t = self._lookahead()
            if t.type is Tokens.COMMA:
                self._consume()
                value = self._value()
                values.append(value['value'])
                if value['default']:
                    default = count
            else:
                break
        return ValueList(values, default)

    def _value(self):
        """
        STAR? (STRING | digit)
        """
        is_default = False
        token = self._match(Tokens.DEFAULT_MARKER, Tokens.STRING, Tokens.INTEGER, Tokens.FLOAT)
        if token.type is Tokens.DEFAULT_MARKER:
            is_default = True
            token = self._match(Tokens.STRING, Tokens.INTEGER, Tokens.FLOAT)
        if token.type is Tokens.STRING:
            return {'value': token.value, 'default': is_default}
        else:
            return {'value': _to_number(token.value), 'default': is_default}

    def _value_range(self):
        """
        digit COLON digit (COLON digit)? (STAR digit)?
        """
        start = self._digit().value
        self._match(Tokens.COLON)
        end = self._digit().value
        step, default = None, None
        token = self._lookahead()
        if token.type is Tokens.COLON:
            self._consume()
            step = self._digit().value
            token = self._lookahead()
        if token.type is Tokens.DEFAULT_MARKER:
            self._consume()
            default = self._digit().value
        return ValueRange(
            _to_number(start),
            _to_number(end),
            _to_number(step) if step is not None else step,
            _to_number(default) if default is not None else default,
        )

    def _digit(self):
        return self._match(Tokens.INTEGER, Tokens.FLOAT)
