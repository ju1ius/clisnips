"""
GRAMMAR
=======
documentation:  header param_list code
header:         T_TEXT*
param_list:     param_doc*
code:           T_CODEMARK T_TEXT T_CODEMARK
param_doc:      T_LBRACE param_id? T_RBRACE typehint? valuehint? doctext?
param_id:       identifier | flag
identifier:     T_IDENTIFIER | T_INTEGER
flag:           T_FLAG
typehint:       T_LPAREN T_IDENTIFIER T_RPAREN
valuehint:      T_LBRACK (value_list | value_range) T_RBRACK
value_list:     value (T_COMMA value)*
value_range:    T_DIGIT T_COLON digit (T_COLON digit)? (T_STAR digit)?
value:          T_STAR? (T_STRING | digit)
digit:          T_INTEGER | T_FLOAT
"""

from collections import OrderedDict

from ..exceptions import ParsingError
from .doc_tokens import *
from .doc_nodes import *
from .doc_lexer import Lexer


def _to_number(string):
    if '.' in string:
        return float(string)
    return int(string)


class LLkParser(object):
#{{{
    def __init__(self, lexer, k=2):
        self._K = k
        self.lexer = lexer

    def reset(self):
        self.lexer.reset()
        self.tokenstream = iter(self.lexer)
        self.position = 0
        self._buffer = [None for i in xrange(self._K)]
        for i in xrange(self._K):
            self._consume()

    def _match(self, *types):
        token = self._ensure(*types)
        self._consume()
        return token

    def _ensure(self, *types):
        token = self._lookahead()
        matches = False
        if token.type not in types:
            self._unexpected_token(token, *types)
        return token

    def _consume(self):
        try:
            token = next(self.tokenstream)
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
        expected = ', '.join(token_name(t) for t in expected)
        raise ParsingError(
            'Unexpected token: {} (expected {})'.format(token, expected)
        )
#}}}


class Parser(LLkParser):

    def __init__(self, lexer):
        super(Parser, self).__init__(lexer, 2)

    def parse(self):
#{{{
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
#}}}

    def _text(self):
        """
        T_TEXT*
        """
#{{{
        text = []
        while True:
            t = self._lookahead()
            if t.type == T_TEXT:
                self._consume()
                text.append(t.value)
            else:
                break
        return ''.join(text)
#}}}

    def _param_list(self):
        """
        param_doc*
        """
#{{{
        while True:
            t = self._lookahead()
            if t.type == T_LBRACE:
                yield self._param_doc()
            else:
                break
#}}}

    def _code(self):
        """
        T_CODEBLOCK*
        """
# {{{
        code_blocks = []
        while self._lookahead_type() == T_CODEMARK:
            self._match(T_CODEMARK)
            code = self._match(T_TEXT).value
            try:
                block = CodeBlock(code)
            except SyntaxError as err:
                msg = 'Syntax error in code block: %r' % code
                msg += '\n' + str(err)
                raise ParsingError(msg)
            except TypeError as err:
                msg = 'Null bytes in code block: %r' % code
                raise ParsingError(msg)
            else:
                code_blocks.append(block)
            self._match(T_CODEMARK)
        return code_blocks
# }}}

    def _param_doc(self):
        """
        T_LBRACE param_id T_RBRACE
        typehint? valuehint? doctext?
        """
#{{{
        typehint, valuehint, text = None, None, None
        self._match(T_LBRACE)
        param = self._param_id()
        self._match(T_RBRACE)

        token = self._lookahead()
        if token.type == T_LPAREN:
            if param.typehint == 'flag':
                raise ParsingError('A flag cannot have a type hint.')
            param.typehint = self._typehint()
            token = self._lookahead()
        if token.type == T_LBRACK:
            if param.typehint == 'flag':
                raise ParsingError('A flag cannot have a value hint.')
            param.valuehint = self._valuehint()
            token = self._lookahead()
        if token.type == T_TEXT:
            param.text = self._text()
        return param
#}}}

    def _param_id(self):
# {{{
        # no identifier, try automatic numbering
        if self._lookahead_type() == T_RBRACE:
            if self._has_numeric_field:
                raise ParsingError(
                    'cannot switch from manual to automatic field numbering'
                )
            self._auto_field_count += 1
            return Parameter(self._auto_field_count)
        token = self._match(T_IDENTIFIER, T_INTEGER, T_FLAG)
        # it's a flag
        if token.type == T_FLAG:
            param = Parameter(token.value)
            param.typehint = 'flag'
            return param
        # it's an integer, check that numbering is correct
        if token.type == T_INTEGER:
            if self._auto_field_count > -1:
                raise ParsingError(
                    'cannot switch from automatic to manual field numbering'
                )
            self._has_numeric_field = True
        return Parameter(token.value)
# }}}

    def _typehint(self):
        """
        T_LPAREN T_IDENTIFIER T_RPAREN
        """
#{{{
        self._match(T_LPAREN)
        hint = self._match(T_IDENTIFIER).value
        self._match(T_RPAREN)
        return hint 
#}}}

    def _valuehint(self):
        """
        T_LBRACK (value_list | value_range) T_RBRACK
        """
#{{{
        self._match(T_LBRACK)
        token = self._lookahead()
        if (
            token.type in (T_INTEGER, T_FLOAT)
            and self._lookahead_type(2) == T_COLON
        ):
            valuehint = self._value_range()
        else:
            valuehint = self._value_list()
        self._match(T_RBRACK)
        return valuehint
#}}}

    def _value_list(self):
        """
        value (T_COMMA value)*
        """
#{{{
        values = []
        default, count = 0, 0
        initial = self._value()
        values.append(initial['value'])
        while True:
            count += 1
            t = self._lookahead()
            if t.type == T_COMMA:
                self._consume()
                value = self._value()
                values.append(value['value'])
                if value['default']:
                    default = count
            else:
                break
        return ValueList(values, default)
#}}}

    def _value(self):
        """
        T_STAR? (T_STRING | digit)
        """
#{{{
        is_default = False
        token = self._match(T_STAR, T_STRING, T_INTEGER, T_FLOAT)
        if token.type == T_STAR:
            is_default = True
            token = self._match(T_STRING, T_INTEGER, T_FLOAT)
        if token.type == T_STRING:
            return {'value': token.value, 'default': is_default}
        else:
            return {'value': _to_number(token.value), 'default': is_default}
#}}}

    def _value_range(self):
        """
        digit T_COLON digit (T_COLON digit)? (T_STAR digit)?
        """
#{{{
        start = self._digit().value
        self._match(T_COLON)
        end = self._digit().value
        step, default = None, None
        token = self._lookahead()
        if token.type == T_COLON:
            self._consume()
            step = self._digit().value
            token = self._lookahead()
        if token.type == T_STAR:
            self._consume()
            default = self._digit().value
        return ValueRange(
            _to_number(start),
            _to_number(end),
            _to_number(step) if step is not None else step,
            _to_number(default) if default is not None else default,
        )
#}}}

    def _digit(self):
        return self._match(T_INTEGER, T_FLOAT)


def parse(docstring):
    return Parser(Lexer(docstring)).parse()
