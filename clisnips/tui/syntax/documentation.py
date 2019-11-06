import re

from pygments.formatter import Formatter
from pygments.lexer import RegexLexer, bygroups, using
from pygments.lexers.python import Python3Lexer
from pygments.token import *
from pygments import highlight

__all__ = ['highlight_documentation']

Parameter = Token.Parameter
TypeHint = Token.TypeHint
ValueHint = Token.ValueHint
ValueHint.Start = ValueHint.Start
ValueHint.End = ValueHint.End
Code = Token.Code
Code.Start = Code.Start
Code.End = Code.End


INTEGER_RX = r'0 | [1-9] \d*'
FLOAT_RX = r'\d* \. \d+'
NUMBER_RX = fr'({FLOAT_RX}) | ({INTEGER_RX})'


class DocLexer(RegexLexer):

    name = 'ClisnipsDoc'
    aliases = 'doc'
    flags = re.X

    tokens = {
        'root': [
            (r'(?m) ^ [\x20\t\f]* (?=\{)', Text, 'param_name'),
            (r'(?m)^```\n', Code.Start, 'code-content'),
            (r'[\w \t\f]+', Text),
            # (r'[ \t\f]+', Whitespace),
        ],
        'param_name': [
            (r'{ [^}]* }', Parameter),
            (r'\s+ (?=\()', Text, 'type_hint'),
            (r'\s+ (?=\[)', Text, 'value_hint'),
        ],
        'type_hint': [
            (r' \( [^)]+ \) ', TypeHint, '#pop'),
        ],
        'value_hint': [
            (r'\[', ValueHint.Start),
            (r']', ValueHint.End, '#pop'),
            (r' " (\\.|[^"])* "', String),
            (r" ' (\\.|[^'])* ' ", String),
            (NUMBER_RX, Number),
            (r'(?-x: +)', Whitespace),
            (r'[,*:]', Punctuation),
        ],
        'code-content': [
            (r'(?m) (?<!^```) ((?:.|\n)+) (^```\n)', bygroups(using(Python3Lexer), Code.End), '#pop'),
        ],
    }


class DocFormatter(Formatter):

    doc_scheme = {
        Text: 'doc:default',
        Whitespace: 'doc:default',
        Punctuation: 'doc:punctuation',
        Parameter: 'doc:parameter',
        ValueHint.Start: 'doc:value-hint',
        ValueHint.End: 'doc:value-hint',
        String: 'doc:string',
        Number: 'doc:number',
        TypeHint: 'doc:type-hint',
        Code.Start: 'doc:code-fence',
        Code.End: 'doc:code-fence',
    }
    python_scheme = {
        Text: 'python:default',
        Comment: 'python:comment',
        Comment.Hashbang: 'python:comment',
        Comment.Single: 'python:comment',
        Keyword: 'python:keyword',
        Keyword.Namespace: 'python:keyword',
        Keyword.Constant: 'python:keyword',
        Operator.Word: 'python:keyword',
        String: 'python:string',
        String.Escape: 'python:string:escape',
        String.Double: 'python:string',
        String.Single: 'python:string',
        String.Affix: 'python:string',
        String.Interpol: 'python:string:interp',
        String.Doc: 'python:comment',
        Number: 'python:number',
        Number.Float: 'python:number',
        Number.Integer: 'python:number',
        Number.Interger.Long: 'python:number',
        Number.Hex: 'python:number',
        Number.Oct: 'python:number',
        Number.Bin: 'python:number',
        Name: 'python:name',
        Name.Function: 'python:function',
        Name.Function.Magic: 'python:function',
        Name.Exception: 'python:function',
        Name.Class: 'python:class',
        Name.Decorator: 'python:decorator',
        Name.Builtin: 'python:function',
        Name.Builtin.Pseudo: 'python:keyword',
    }

    def get_doc_attr(self, key):
        try:
            return self.doc_scheme[key]
        except KeyError:
            return 'doc:default'

    def get_code_attr(self, key):
        try:
            return self.python_scheme[key]
        except KeyError:
            return 'python:default'

    def format(self, token_stream, outfile):
        in_code = False
        for token_type, value in token_stream:
            if token_type is Code.Start:
                in_code = True
                style = self.get_doc_attr(token_type)
            elif token_type is Code.End:
                in_code = False
                style = self.get_doc_attr(token_type)
            elif in_code:
                style = self.get_code_attr(token_type)
            else:
                style = self.get_doc_attr(token_type)
            outfile.write((style, value))


class UrwidMarkupWriter:

    def __init__(self):
        self._markup = []

    def write(self, text_attr):
        self._markup.append(text_attr)

    def clear(self):
        self._markup = []

    def get_markup(self):
        return self._markup


_lexer = DocLexer()
_formatter = DocFormatter()
_writer = UrwidMarkupWriter()


def highlight_documentation(text: str):
    _writer.clear()
    highlight(text, _lexer, _formatter, _writer)
    return _writer.get_markup()
