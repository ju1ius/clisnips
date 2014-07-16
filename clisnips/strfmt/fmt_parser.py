import re
from string import Formatter

from ..exceptions import ParsingError


FIELD_NAME_RX = re.compile(r'''
^
(\d+|[_a-zA-Z]\w*)      # arg_name
(?:
    \.[_a-zA-Z]\w*      # getattr 
    |
    \[ \d+ | [^\]]+ \]  # getitem
)*
$
''', re.X)
__lexer = Formatter()


def parse(text):
    try:
        stream = __lexer.parse(text)
    except Exception as err:
        raise ParsingError(str(err))
    fields = []
    auto_count = -1
    has_explicit_numeric_field = False
    for prefix, param, spec, conv in stream:
        if param is None:
            continue
        name = ''
        if param:
            m = FIELD_NAME_RX.match(param)
            if not m:
                raise ParsingError('Invalid replacement field %r' % param)
            name = m.group(1)
        if not name:
            if has_explicit_numeric_field:
                raise ParsingError('Cannot switch from manual '
                                   'to automatic field numbering')
            auto_count += 1
            name = auto_count
        elif name.isdigit():
            has_explicit_numeric_field = True
            if auto_count > -1:
                raise ParsingError('Cannot switch from automatic '
                                   'to manual field numbering')
        fields.append({
            'name': name,
            'identifier': param,
            'spec': spec,
            'conv': conv
        })
    return fields


# Begin Deprecated code

from .doc_tokens import *


PARAM_NAME_RX = re.compile(r'\d+|[_a-zA-Z]\w*')


class Lexer(object):

    def __init__(self, text):
        self.text = text

    def __iter__(self):
        stream = __lexer.parse(self.text)
        self.pos = 0
        self.line = self.col = 1
        for prefix, param, spec, conv in stream:
            if prefix:
                yield self._handle_text(prefix)
            if param is None:
                continue
            yield self._handle_field(param, spec, conv)

    def _handle_text(self, text):
        t = self.init_token(T_TEXT, text)
        l = len(text)
        self.pos += l
        last_line_pos = text.rfind('\n')
        if last_line_pos != -1:
            self.line += text.count('\n')
            self.col = l - last_line_pos - 1
        else:
            self.col += l
        return self.finalize_token(t)

    def _handle_field(self, param, spec, conv):
        #FIXME:
        # the docstring parser doesn't support item/attribute access,
        # or exotic characters (e.g. linebreaks) in identifiers.
        # For now we just raise an exception.
        name = ''
        if param:
            m = PARAM_NAME_RX.match(param)
            name = m.group(0)
        value = {
            'name': name,
            'identifier': param,
            'spec': spec,
            'conv': conv
        }
        t = self.init_token(T_PARAM, value)
        l = len(param) + 2  # account for the "{}" delimiters
        if spec:
            l += len(spec) + 1  # account for the ":" separator
        if conv:
            l += len(conv) + 1  # account for the "!" separator
        self.pos += l
        self.col += l
        return self.finalize_token(t)

    def init_token(self, type, value=None):
        token = Token(type, self.line, self.col, value)
        token.startpos = self.pos
        return token

    def finalize_token(self, token, line=None, col=None, pos=None, value=None):
        if value is not None:
            token.value = value
        token.endpos = pos if pos is not None else self.pos
        token.endline = line if line is not None else self.line
        token.endcol = col if col is not None else self.col
        return token


def __parse(fmt_str):
    auto_count = -1
    has_numeric_field = False
    fields = []
    for token in Lexer(fmt_str):
        if token.type == T_PARAM:
            name = token.value['name']
            if not name:
                if has_numeric_field:
                    raise ParsingError('Cannot switch from manual '
                                       'to automatic field numbering')
                auto_count += 1
                token.value['name'] = auto_count
            else:
                try:
                    name = int(name)
                    is_numeric = has_numeric_field = True
                except ValueError:
                    is_numeric = False
                if is_numeric and auto_count > -1:
                    raise ParsingError('Cannot switch from automatic '
                                       'to manual field numbering')
            fields.append(token.value)
    return fields
