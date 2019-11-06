from string import Formatter as _CommandParser

from ..urwid_types import TextMarkup
from ...exceptions import ParsingError


def highlight_command(cmd_string) -> TextMarkup:
    if not cmd_string:
        return ''
    try:
        # We have to convert to list, otherwise exceptions will be throw during iteration
        tokens = list(_CommandParser().parse(cmd_string))
    except Exception as err:
        raise ParsingError.from_exception(err)
    markup = []
    for prefix, param, spec, conv in tokens:
        markup.append(('cmd:default', prefix))
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
