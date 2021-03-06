import re
from string import Formatter

from clisnips.exceptions import ParsingError
from .nodes import CommandTemplate, Text, Field


_FIELD_NAME_RX = re.compile(r'''
^
    (--? [a-zA-Z0-9] [\w-]*)    # cli flag
    |
    ( \d+ | [_a-zA-Z]\w* )      # digit or identifier
$
''', re.X)

__lexer = Formatter()


def parse(text):
    try:
        stream = list(__lexer.parse(text))
    except Exception as err:
        raise ParsingError.from_exception(err)
    nodes = []
    auto_count = -1
    has_explicit_numeric_field = False
    pos = 0
    for prefix, field_name, format_spec, conversion in stream:
        end = pos + len(prefix)
        nodes.append(Text(prefix, pos, end))
        pos = end
        if field_name is None:
            continue
        node = Field('', pos, pos + 2)
        if field_name:
            m = _FIELD_NAME_RX.match(field_name)
            if not m:
                raise ParsingError(f'Invalid replacement field {field_name!r}')
            node.name = m.group(1) if m.group(1) else m.group(2)
            node.end += len(node.name)
        if not node.name:
            if has_explicit_numeric_field:
                raise ParsingError('Cannot switch from manual to automatic field numbering')
            auto_count += 1
            node.name = str(auto_count)
        elif node.name.isdigit():
            has_explicit_numeric_field = True
            if auto_count > -1:
                raise ParsingError('Cannot switch from automatic to manual field numbering')
        if format_spec:
            _check_format_spec(format_spec)
            node.format_spec = format_spec
            node.end += len(format_spec) + 1
        if conversion:
            node.conversion = conversion
            node.end += 2
        pos = node.end
        nodes.append(node)
    return CommandTemplate(text, nodes)


def _check_format_spec(format_spec):
    """
    PEP 3101 supports replacement fields inside format specifications.
    Since it would complicate the implementation, for a feature most likely not needed,
    we choose not to support it.
    see: https://www.python.org/dev/peps/pep-3101
    """
    for prefix, field_name, format_spec, conversion in __lexer.parse(format_spec):
        if field_name is not None:
            raise ParsingError('Replacement fields in format specifications are not supported')
