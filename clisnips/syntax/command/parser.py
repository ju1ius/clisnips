import re
from string import Formatter

from clisnips.exceptions import CommandParsingError

from .nodes import CommandTemplate, Field, Text

_FIELD_NAME_RX = re.compile(r'''
^
    (--? [a-zA-Z0-9] [\w-]*)    # cli flag
    |
    ( \d+ | [_a-zA-Z]\w* )      # digit or identifier
$
''', re.X)

__lexer = Formatter()


def parse(subject: str) -> CommandTemplate:
    try:
        stream = list(__lexer.parse(subject))
    except Exception as err:
        raise CommandParsingError(str(err), subject) from err
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

        name, start, end = '', pos, pos + 2
        if field_name:
            m = _FIELD_NAME_RX.match(field_name)
            if not m:
                raise CommandParsingError(f'Invalid replacement field {field_name!r}', subject)
            name = m.group(1) if m.group(1) else m.group(2)
            end += len(name)
        if not name:
            if has_explicit_numeric_field:
                raise CommandParsingError('Cannot switch from manual to automatic field numbering', subject)
            auto_count += 1
            name = str(auto_count)
        elif name.isdigit():
            has_explicit_numeric_field = True
            if auto_count > -1:
                raise CommandParsingError('Cannot switch from automatic to manual field numbering', subject)
        if format_spec:
            _check_format_spec(format_spec)
            end += len(format_spec) + 1
        if conversion:
            end += 2
        pos = end
        nodes.append(Field(name, start, end, format_spec, conversion))
    return CommandTemplate(subject, nodes)


def _check_format_spec(format_spec: str):
    """
    PEP 3101 supports replacement fields inside format specifications.
    Since it would complicate the implementation, for a feature most likely not needed,
    we choose not to support it.
    see: https://www.python.org/dev/peps/pep-3101
    """
    for prefix, name, spec, conversion in __lexer.parse(format_spec):
        if name is not None:
            raise CommandParsingError(
                'Replacement fields in format specifications are not supported',
                format_spec,
            )
