import re

from pygments import highlight
from pygments.formatter import Formatter
from pygments.lexer import RegexLexer, bygroups, using
from pygments.lexers.python import Python3Lexer
from pygments.token import Comment, Keyword, Name, Number, Operator, Punctuation, String, Text, Token, Whitespace

from .writer import UrwidMarkupWriter

__all__ = ('highlight_documentation',)

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
NUMBER_RX = rf'({FLOAT_RX}) | ({INTEGER_RX})'


class DocLexer(RegexLexer):
    name = 'ClisnipsDoc'
    aliases = 'doc'
    flags = re.X

    tokens = {
        'root': [
            (r'(?m) ^ [\x20\t\f]* (?=\{)', Text, 'param_name'),
            (r'(?m)^```\n', Code.Start, 'code-content'),
            (r'.+', Text),
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
            (r'[,:]', Punctuation),
            (r'=>', ValueHint.Default),
        ],
        'code-content': [
            (r'(?m) (?<!^```) ((?:.|\n)+) (^```\n)', bygroups(using(Python3Lexer), Code.End), '#pop'),
        ],
    }


class DocFormatter(Formatter):
    doc_scheme = {
        Text: 'syn:doc:default',
        Whitespace: 'syn:doc:default',
        Punctuation: 'syn:doc:punctuation',
        Parameter: 'syn:doc:parameter',
        ValueHint.Start: 'syn:doc:value-hint',
        ValueHint.End: 'syn:doc:value-hint',
        ValueHint.Default: 'syn:doc:value-hint:default',
        String: 'syn:doc:string',
        Number: 'syn:doc:number',
        TypeHint: 'syn:doc:type-hint',
        Code.Start: 'syn:doc:code-fence',
        Code.End: 'syn:doc:code-fence',
    }
    python_scheme = {
        Text: 'syn:py:default',
        Comment: 'syn:py:comment',
        Comment.Hashbang: 'syn:py:comment',
        Comment.Single: 'syn:py:comment',
        Keyword: 'syn:py:keyword',
        Keyword.Namespace: 'syn:py:keyword',
        Keyword.Constant: 'syn:py:keyword',
        Operator.Word: 'syn:py:keyword',
        String: 'syn:py:string',
        String.Escape: 'syn:py:string:escape',
        String.Double: 'syn:py:string',
        String.Single: 'syn:py:string',
        String.Affix: 'syn:py:string',
        String.Interpol: 'syn:py:string:interp',
        String.Doc: 'syn:py:comment',
        Number: 'syn:py:number',
        Number.Float: 'syn:py:number',
        Number.Integer: 'syn:py:number',
        Number.Interger.Long: 'syn:py:number',
        Number.Hex: 'syn:py:number',
        Number.Oct: 'syn:py:number',
        Number.Bin: 'syn:py:number',
        Name: 'syn:py:name',
        Name.Function: 'syn:py:function',
        Name.Function.Magic: 'syn:py:function',
        Name.Exception: 'syn:py:function',
        Name.Class: 'syn:py:class',
        Name.Decorator: 'syn:py:decorator',
        Name.Builtin: 'syn:py:function',
        Name.Builtin.Pseudo: 'syn:py:keyword',
    }

    def get_doc_attr(self, key):
        try:
            return self.doc_scheme[key]
        except KeyError:
            return 'syn:doc:default'

    def get_code_attr(self, key):
        try:
            return self.python_scheme[key]
        except KeyError:
            return 'syn:py:default'

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


_lexer = DocLexer(encoding='utf8', stripall=True, ensurenl=True)
_formatter = DocFormatter()
_writer = UrwidMarkupWriter()


def highlight_documentation(text: str):
    if not text:
        return ''
    _writer.clear()
    highlight(text, _lexer, _formatter, _writer)
    return _writer.get_markup()
