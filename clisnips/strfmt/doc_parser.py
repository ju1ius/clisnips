"""
GRAMMAR
=======
documentation:  header param_list code
header:         T_TEXT*
param_list:     param_doc*
code:           T_CODEBLOCK*
param_doc:      T_LBRACE T_IDENT? T_RBRACE typehint? valuehint? doctext?
typehint:       T_LPAREN T_IDENT T_RPAREN
valuehint:      T_LBRACK (value_list | value_range) T_RBRACK
value_list:     value (T_COMMA value)*
value_range:    T_DIGIT T_RANGE_SEP T_DIGIT (T_COLON T_DIGIT)? (T_STAR T_DIGIT)?
value:          T_STAR? (T_STRING | T_DIGIT)
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
        self._ast = Documentation()
        self._ast.header = self._text()
        for param in self._param_list():
            self._ast.parameters.append(param)
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
        params = []
        while True:
            t = self._lookahead()
            if t.type == T_LBRACE:
                param = self._param_doc()
                params.append(param)
            else:
                break
        return params
#}}}

    def _code(self):
        """
        T_CODEBLOCK*
        """
# {{{
        code_blocks = []
        while True:
            t = self._lookahead()
            if t.type == T_CODEBLOCK:
                self._consume()
                try:
                    block = CodeBlock(t.value)
                except SyntaxError as err:
                    msg = 'Syntax error in code block: %s' % repr(t.value)
                    msg += '\n' + str(err)
                    raise ParsingError(msg)
                except TypeError as err:
                    msg = 'Null bytes in code block: %s' % repr(t.value)
                    raise ParsingError(msg)
                else:
                    code_blocks.append(block)
            else:
                break
        return code_blocks
# }}}

    def _param_doc(self):
        """
        T_LBRACE T_IDENT? T_RBRACE typehint? valuehint? doctext?
        """
#{{{
        name, typehint, valuehint, text = '', None, None, None
        self._match(T_LBRACE)
        t = self._lookahead()
        if t.type == T_IDENT:
            self._consume()
            name = t.value
        self._match(T_RBRACE)
        t = self._lookahead()
        if t.type == T_TYPEHINT:
            typehint = self._typehint()
            t = self._lookahead()
        if t.type == T_LBRACK:
            valuehint = self._valuehint()
            t = self._lookahead()
        if t.type == T_TEXT:
            text = self._text()
        return Parameter(name, typehint, valuehint, text)
#}}}

    def _typehint(self):
        """
        T_LPAREN T_IDENT T_RPAREN
        """
#{{{
        t = self._match(T_TYPEHINT)
        return t.value
#}}}

    def _valuehint(self):
        """
        T_LBRACK (value_list | value_range) T_RBRACK
        """
#{{{
        self._match(T_LBRACK)
        t = self._lookahead()
        if t.type == T_DIGIT and self._lookahead_type(2) == T_RANGE_SEP:
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
        if not initial:
            return values
        values.append(initial['value'])
        while True:
            count += 1
            t = self._lookahead()
            if t.type == T_COMMA:
                self._consume()
                value = self._value()
                if value:
                    values.append(value['value'])
                    if value['default']:
                        default = count
                else:
                    break
            else:
                break
        return ValueList(values, default)
#}}}

    def _value(self):
        """
        T_STAR? (T_STRING | T_DIGIT)
        """
#{{{
        is_default = False
        t = self._lookahead()
        if t.type == T_STAR:
            is_default = True
            self._consume()
            t = self._lookahead()
        if t.type == T_STRING:
            self._consume()
            return {'value': t.value, 'default': is_default}
        elif t.type == T_DIGIT:
            self._consume()
            return {'value': _to_number(t.value), 'default': is_default}
#}}}

    def _value_range(self):
        """
        T_DIGIT T_RANGE_SEP T_DIGIT (T_COLON T_DIGIT)? (T_STAR T_DIGIT)?
        """
#{{{
        start = self._match(T_DIGIT).value
        self._match(T_RANGE_SEP)
        end = self._match(T_DIGIT).value
        step, default = None, None
        t = self._lookahead()
        if t.type == T_COLON:
            self._consume()
            step = self._match(T_DIGIT).value
            t = self._lookahead()
        if t.type == T_STAR:
            self._consume()
            default = self._match(T_DIGIT).value
        return ValueRange(
            _to_number(start),
            _to_number(end),
            _to_number(step) if step is not None else step,
            _to_number(default) if default is not None else default,
        )
#}}}


def parse(docstring):
    return Parser(Lexer(docstring)).parse()
