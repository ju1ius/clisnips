import re
from string import Formatter

from ..exceptions import ParsingError


FIELD_NAME_RX = re.compile(r'''
^(?:
    (--?[a-zA-Z0-9][\w-]*)   # cli flag
) | (?:
    (\d+|[_a-zA-Z]\w*)      # arg_name
    (?:
        \.[_a-zA-Z]\w*      # getattr 
        |
        \[ \d+ | [^\]]+ \]  # getitem
    )*
)$
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
            name = m.group(1) if m.group(1) else m.group(2)
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
