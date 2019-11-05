from string import Formatter as _CommandParser
from textwrap import dedent as _dedent

from .urwid_types import TextMarkup
from ..strfmt.doc_parser import parse as _parse_documentation
from ..utils import iterable


def highlight_documentation(doc_string) -> TextMarkup:
    if not doc_string:
        return ''
    ast = _parse_documentation(doc_string)
    markup = []
    if ast.header:
        markup.append(('doc:header', _dedent(ast.header)))
    for param in ast.parameters.values():
        field = [('doc:param:name', f'{{{param.name}}}')]
        if param.typehint:
            field.append(('doc:param:type-hint', f'({param.typehint})'))
        if param.valuehint:
            field.append(('doc:param:value-hint', f'{param.valuehint}'))
        if param.text:
            field.append(('doc:param:text', param.text))
        markup.append(list(iterable.join(' ', field)))
    for code in ast.code_blocks:
        markup.append('```\n')
        # TODO python highlighting
        markup.append(('doc:code', str(code)))
        markup.append('```\n')
    return markup


def highlight_command(cmd_string) -> TextMarkup:
    if not cmd_string:
        return ''
    tokens = _CommandParser().parse(cmd_string)
    markup = []
    for prefix, param, spec, conv in tokens:
        markup.append(prefix)
        if not param:
            continue
        field = [('cmd:param', '{%s' % param)]
        if conv:
            field.append(('cmd:conv', f'!{conv}'))
        if spec:
            field.append(('cmd:spec', f':{spec}'))
        field.append(('cmd:param', '}'))
        markup.append(field)
    return markup
