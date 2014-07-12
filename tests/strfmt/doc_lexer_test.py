import unittest

from clisnips.strfmt.doc_tokens import *
from clisnips.strfmt.doc_lexer import Lexer


class DocLexerTest(unittest.TestCase):

    def assertTokenListEqual(self, actual_tokens, expected_tokens):
        self.assertEqual(len(actual_tokens), len(expected_tokens))
        for i, exp in enumerate(expected_tokens):
            token = actual_tokens[i]
            for attr in exp.keys():
                actual = getattr(token, attr)
                expected = exp[attr]
                self.assertEqual(
                    actual,
                    expected,
                    'Expected token.{} to equal {!r}, got {!r}'.format(
                        attr,
                        token_name(expected) if attr == 'type' else expected,
                        token_name(actual) if attr == 'type' else actual
                    )
                )

    def _tokenize(self, text):
        lexer = Lexer(text)
        return [t for t in Lexer(text)]
    
    def testFreeTextOnly(self):
        text = """
            This is the global description of the command.
            It's all text until a {parameter} is seen.
            A {param} must start a line (possibly indented).
        """
        lexer = iter(Lexer(text))
        token = next(lexer)
        self.assertEqual(token.type, T_TEXT)
        self.assertEqual(token.value, text)

    def testParamOnly(self):
        text = '{par1}\n{par2}'
        tokens = [t for t in Lexer(text)]
        expected = [
            {'type': T_LBRACE},
            {'type': T_IDENT, 'value': 'par1'},
            {'type': T_RBRACE},
            {'type': T_TEXT, 'value': '\n'},
            {'type': T_LBRACE},
            {'type': T_IDENT, 'value': 'par2'},
            {'type': T_RBRACE},
            {'type': T_EOF}
        ]
        self.assertTokenListEqual(tokens, expected)

    def testTypeHintOnly(self):
        text = '{par1} ( string )'
        tokens = [t for t in Lexer(text)]
        expected = [
            {'type': T_LBRACE},
            {'type': T_IDENT, 'value': 'par1'},
            {'type': T_RBRACE},
            {'type': T_TYPEHINT, 'value': 'string'},
            {'type': T_EOF}
        ]
        self.assertTokenListEqual(tokens, expected)
        #FIXME: test that invalid typehint is skipped

    def testValueHintStringList(self):
        # string list
        text = '{par1} ["value1", *"value2"]'
        tokens = [t for t in Lexer(text)]
        expected = [
            {'type': T_LBRACE},
            {'type': T_IDENT, 'value': 'par1'},
            {'type': T_RBRACE},
            {'type': T_LBRACK},
            {'type': T_STRING, 'value': 'value1'},
            {'type': T_COMMA},
            {'type': T_STAR},
            {'type': T_STRING, 'value': 'value2'},
            {'type': T_RBRACK},
            {'type': T_EOF}
        ]
        self.assertTokenListEqual(tokens, expected)

    def testValueHintDigitList(self):
        # digit list
        text = '{par1} [1, *-2, 0.3]'
        tokens = [t for t in Lexer(text)]
        expected = [
            {'type': T_LBRACE},
            {'type': T_IDENT, 'value': 'par1'},
            {'type': T_RBRACE},
            {'type': T_LBRACK},
            {'type': T_DIGIT, 'value': '1'},
            {'type': T_COMMA},
            {'type': T_STAR},
            {'type': T_DIGIT, 'value': '-2'},
            {'type': T_COMMA},
            {'type': T_DIGIT, 'value': '0.3'},
            {'type': T_RBRACK},
            {'type': T_EOF}
        ]
        self.assertTokenListEqual(tokens, expected)

    def testValueHintRange(self):
        # simple range 
        text = '{par1} [1..5]'
        tokens = [t for t in Lexer(text)]
        expected = [
            {'type': T_LBRACE},
            {'type': T_IDENT, 'value': 'par1'},
            {'type': T_RBRACE},
            {'type': T_LBRACK},
            {'type': T_DIGIT, 'value': '1'},
            {'type': T_RANGE_SEP},
            {'type': T_DIGIT, 'value': '5'},
            {'type': T_RBRACK},
            {'type': T_EOF}
        ]
        self.assertTokenListEqual(tokens, expected)
        # range with step
        text = '{par1} [1..10:2]'
        tokens = [t for t in Lexer(text)]
        expected = [
            {'type': T_LBRACE},
            {'type': T_IDENT, 'value': 'par1'},
            {'type': T_RBRACE},
            {'type': T_LBRACK},
            {'type': T_DIGIT, 'value': '1'},
            {'type': T_RANGE_SEP},
            {'type': T_DIGIT, 'value': '10'},
            {'type': T_COLON},
            {'type': T_DIGIT, 'value': '2'},
            {'type': T_RBRACK},
            {'type': T_EOF}
        ]
        self.assertTokenListEqual(tokens, expected)
        # range with step and default
        text = '{ par1 } [1 .. 10 : 2 * 5]'
        tokens = [t for t in Lexer(text)]
        expected = [
            {'type': T_LBRACE},
            {'type': T_IDENT, 'value': 'par1'},
            {'type': T_RBRACE},
            {'type': T_LBRACK},
            {'type': T_DIGIT, 'value': '1'},
            {'type': T_RANGE_SEP},
            {'type': T_DIGIT, 'value': '10'},
            {'type': T_COLON},
            {'type': T_DIGIT, 'value': '2'},
            {'type': T_STAR},
            {'type': T_DIGIT, 'value': '5'},
            {'type': T_RBRACK},
            {'type': T_EOF}
        ]
        self.assertTokenListEqual(tokens, expected)

    def testFreeTextAfterParam(self):
        text = '{ par1 } Some free text (wow, [snafu])'
        tokens = [t for t in Lexer(text)]
        expected = [
            {'type': T_LBRACE},
            {'type': T_IDENT, 'value': 'par1'},
            {'type': T_RBRACE},
            {'type': T_TEXT},
            {'type': T_EOF}
        ]
        self.assertTokenListEqual(tokens, expected)

        text = '''{ par1 } Some free text (wow, [snafu])
            {par2} (hint) Other text
            {par3} (hint) ["foo"] Yet another doctext
        '''
        tokens = [t for t in Lexer(text)]
        expected = [
            {'type': T_LBRACE},
            {'type': T_IDENT, 'value': 'par1'},
            {'type': T_RBRACE},
            {'type': T_TEXT},
            {'type': T_LBRACE},
            {'type': T_IDENT, 'value': 'par2'},
            {'type': T_RBRACE},
            {'type': T_TYPEHINT, 'value': 'hint'},
            {'type': T_TEXT},
            {'type': T_LBRACE},
            {'type': T_IDENT, 'value': 'par3'},
            {'type': T_RBRACE},
            {'type': T_TYPEHINT, 'value': 'hint'},
            {'type': T_LBRACK},
            {'type': T_STRING, 'value': 'foo'},
            {'type': T_RBRACK},
            {'type': T_TEXT},
            {'type': T_EOF}
        ]
        self.assertTokenListEqual(tokens, expected)

    def testCodeBlock(self):
        text = '''
```
import foo, bar
params['foo'] = '{bar}'
```'''
        tokens = [t for t in Lexer(text)]
        expected = [
            {'type': T_TEXT},
            {'type': T_CODEBLOCK},
            {'type': T_EOF}
        ]
        self.assertTokenListEqual(tokens, expected)

        text = '''{par1} Some text
```
import foo, bar
params['foo'] = '{bar}'
```
    {par2} Other text.
        '''
        tokens = [t for t in Lexer(text)]
        expected = [
            {'type': T_LBRACE},
            {'type': T_IDENT, 'value': 'par1'},
            {'type': T_RBRACE},
            {'type': T_TEXT},
            {'type': T_CODEBLOCK},
            {'type': T_TEXT},
            {'type': T_LBRACE},
            {'type': T_IDENT, 'value': 'par2'},
            {'type': T_RBRACE},
            {'type': T_TEXT},
            {'type': T_EOF}
        ]
        self.assertTokenListEqual(tokens, expected)
