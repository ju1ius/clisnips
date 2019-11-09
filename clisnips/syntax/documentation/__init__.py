from clisnips.syntax.documentation.lexer import Lexer
from clisnips.syntax.documentation.nodes import Documentation
from clisnips.syntax.documentation.parser import Parser


def parse(docstring: str) -> Documentation:
    return Parser(Lexer(docstring)).parse()
