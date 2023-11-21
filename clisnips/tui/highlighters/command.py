import re

from pygments import highlight
from pygments.formatter import Formatter
from pygments.lexer import RegexLexer, bygroups
from pygments.token import Punctuation, Text, Token

from clisnips.tui.urwid_types import TextMarkup

from .writer import UrwidMarkupWriter

Command = Token.Command

IDENTIFIER = r'[a-z][a-z0-]*'
DIGIT = r'\d+'
ARG_NAME = rf'(?: {IDENTIFIER} | {DIGIT} )'
INDEX_STR = r'[^\]]+'
ELEMENT_INDEX = rf'\[ {DIGIT} | {INDEX_STR} \]'


class CommandLexer(RegexLexer):
    name = 'ClisnipsCommand'
    aliases = 'cmd'
    flags = re.X | re.I

    tokens = {
        'root': [
            (r'(?<!{) (?:{{)+', Text),
            (r'{', Command.Start, 'format-string'),
            (r'[^{]+', Text),
        ],
        'format-string': [
            (r'}', Command.End, '#pop'),
            (ARG_NAME, Command.ArgName),
            (rf'(\.) ({IDENTIFIER})', bygroups(Punctuation, Command.Identifier)),
            (rf'(\[) ({ELEMENT_INDEX})', bygroups(Punctuation, Command.ElementIndex)),
            (r'(!) ([rsa])', bygroups(Punctuation, Command.Conversion)),
            (r'(:) ([^}]+)', bygroups(Punctuation, Command.FormatSpec)),
        ],
    }


class CommandFormatter(Formatter):
    color_scheme = {
        Text: 'syn:cmd:default',
        Punctuation: 'syn:cmd:punctuation',
        Command.Start: 'syn:cmd:field-marker',
        Command.End: 'syn:cmd:field-marker',
        Command.ArgName: 'syn:cmd:field-name',
        Command.Identifier: 'syn:cmd:field-name',
        Command.ElementIndex: 'syn:cmd:field-name',
        Command.Conversion: 'syn:cmd:field-conversion',
        Command.FormatSpec: 'syn:cmd:field-format',
    }

    def format(self, token_stream, outfile):
        for token_type, value in token_stream:
            try:
                style = self.color_scheme[token_type]
            except KeyError:
                style = 'syn:cmd:default'
            outfile.write((style, value))


_lexer = CommandLexer(encoding='utf8', stripall=True, ensurenl=False)
_formatter = CommandFormatter()
_writer = UrwidMarkupWriter()


def highlight_command(text: str) -> TextMarkup:
    if not text:
        return ''
    _writer.clear()
    highlight(text, _lexer, _formatter, _writer)
    return _writer.get_markup()
