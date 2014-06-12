from string import Formatter

from ..exceptions import ParsingError
from .doc_tokens import * 


__lexer = Formatter()


def lex(fmt_str):
    stream = __lexer.parse(fmt_str)
    pos = line = col = 0
    for prefix, param, spec, conv in stream:
        if prefix:
            t = Token(T_TEXT, line, col, prefix)
            t.startpos = pos
            l = len(prefix)
            pos += l
            last_line_pos = prefix.rfind('\n')
            if last_line_pos != -1:
                line += prefix.count('\n')
                col = l - last_line_pos - 1
            else:
                col += l
            t.endline, t.endcol, t.endpos = line, col, pos
            yield t
        if param is None:
            continue
        #FIXME:
        # the docstring parser doesn't support item/attribute access,
        # or exotic characters (e.g. linebreaks) in identifiers.
        # For now we just raise an exception.
        value = {'identifier': param, 'spec': spec, 'conv': conv}
        t = Token(T_PARAM, line, col, value)
        t.startpos = pos
        l = len(param) + 2  # account for the "{}" delimiters
        if spec:
            l += len(spec) + 1  # account for the ":" separator
        if conv:
            l += len(conv) + 1  # account for the "!" separator
        pos += l
        col += l
        t.endline, t.endcol, t.endpos = line, col, pos
        yield t


def parse(fmt_str):
    auto_count = -1
    has_numeric_field = False
    for token in lex(fmt_str):
        if token.type == T_PARAM:
            name = token.value['identifier']
            if name == '':
                if has_numeric_field:
                    raise ParsingError(
                        'cannot switch from automatic field numbering '
                        'to manual field specification'
                    )
                auto_count += 1
                token.value['identifier'] = auto_count
            else:
                try:
                    name = int(name)
                    is_numeric = has_numeric_field = True
                except ValueError:
                    is_numeric = False
                if is_numeric and auto_count > -1:
                    raise ParsingError(
                        'cannot switch from automatic field numbering '
                        'to manual field specification'
                    )
        yield token


if __name__ == '__main__':
    import sys 
    fmt_str = 'foo: {}\nbar: {w00t}\nblah: {yay}'
    if len(sys.argv) > 1:
        fmt_str = sys.argv[1]
    for token in parse(fmt_str):
        print token
