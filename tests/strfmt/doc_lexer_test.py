from clisnips.strfmt.doc_lexer import Lexer
from clisnips.strfmt.doc_tokens import *


def assert_token_list_equal(actual_tokens, expected_tokens):
    assert len(actual_tokens) == len(expected_tokens)
    for i, exp in enumerate(expected_tokens):
        token = actual_tokens[i]
        for attr in exp.keys():
            actual = getattr(token, attr)
            expected = exp[attr]
            assert expected == actual, 'Expected token.{} to equal {!r}, got {!r}'.format(
                attr,
                expected.name if attr == 'type' else expected,
                actual.name if attr == 'type' else actual
            )


def tokenize(text):
    return list(Lexer(text))


def test_free_text_only():
    text = """
        This is the global description of the command.
        It's all text until a {parameter} is seen.
        A {param} must start a line (possibly indented).
    """
    lexer = iter(Lexer(text))
    token = next(lexer)
    assert token.type == Tokens.TEXT
    assert token.value == text


def test_param_only():
    text = '{par1}\n{par2}'
    tokens = tokenize(text)
    expected = [
        {'type': Tokens.LEFT_BRACE},
        {'type': Tokens.IDENTIFIER, 'value': 'par1'},
        {'type': Tokens.RIGHT_BRACE},
        {'type': Tokens.TEXT, 'value': '\n'},
        {'type': Tokens.LEFT_BRACE},
        {'type': Tokens.IDENTIFIER, 'value': 'par2'},
        {'type': Tokens.RIGHT_BRACE},
        {'type': Tokens.EOF}
    ]
    assert_token_list_equal(tokens, expected)


def test_flags():
    text = '{-h}\n{--some-flag}'
    tokens = tokenize(text)
    expected = [
        {'type': Tokens.LEFT_BRACE},
        {'type': Tokens.FLAG, 'value': '-h'},
        {'type': Tokens.RIGHT_BRACE},
        {'type': Tokens.TEXT, 'value': '\n'},
        {'type': Tokens.LEFT_BRACE},
        {'type': Tokens.FLAG, 'value': '--some-flag'},
        {'type': Tokens.RIGHT_BRACE},
        {'type': Tokens.EOF}
    ]
    assert_token_list_equal(tokens, expected)


def test_type_hint_only():
    text = '{par1} ( string )'
    tokens = tokenize(text)
    expected = [
        {'type': Tokens.LEFT_BRACE},
        {'type': Tokens.IDENTIFIER, 'value': 'par1'},
        {'type': Tokens.RIGHT_BRACE},
        {'type': Tokens.LEFT_PAREN},
        {'type': Tokens.IDENTIFIER, 'value': 'string'},
        {'type': Tokens.RIGHT_PAREN},
        {'type': Tokens.EOF}
    ]
    assert_token_list_equal(tokens, expected)
    # FIXME: test that invalid type_hint is skipped


def test_value_hint_string_list():
    # string list
    text = '{par1} ["value1", =>"value2"]'
    tokens = tokenize(text)
    expected = [
        {'type': Tokens.LEFT_BRACE},
        {'type': Tokens.IDENTIFIER, 'value': 'par1'},
        {'type': Tokens.RIGHT_BRACE},
        {'type': Tokens.LEFT_BRACKET},
        {'type': Tokens.STRING, 'value': 'value1'},
        {'type': Tokens.COMMA},
        {'type': Tokens.DEFAULT_MARKER},
        {'type': Tokens.STRING, 'value': 'value2'},
        {'type': Tokens.RIGHT_BRACKET},
        {'type': Tokens.EOF}
    ]
    assert_token_list_equal(tokens, expected)


def test_value_hint_digit_list():
    # digit list
    text = '{par1} [1, =>-2, 0.3]'
    tokens = tokenize(text)
    expected = [
        {'type': Tokens.LEFT_BRACE},
        {'type': Tokens.IDENTIFIER, 'value': 'par1'},
        {'type': Tokens.RIGHT_BRACE},
        {'type': Tokens.LEFT_BRACKET},
        {'type': Tokens.INTEGER, 'value': '1'},
        {'type': Tokens.COMMA},
        {'type': Tokens.DEFAULT_MARKER},
        {'type': Tokens.INTEGER, 'value': '-2'},
        {'type': Tokens.COMMA},
        {'type': Tokens.FLOAT, 'value': '0.3'},
        {'type': Tokens.RIGHT_BRACKET},
        {'type': Tokens.EOF}
    ]
    assert_token_list_equal(tokens, expected)


def test_value_hint_range():
    # simple range
    text = '{par1} [1:5]'
    tokens = tokenize(text)
    expected = [
        {'type': Tokens.LEFT_BRACE},
        {'type': Tokens.IDENTIFIER, 'value': 'par1'},
        {'type': Tokens.RIGHT_BRACE},
        {'type': Tokens.LEFT_BRACKET},
        {'type': Tokens.INTEGER, 'value': '1'},
        {'type': Tokens.COLON},
        {'type': Tokens.INTEGER, 'value': '5'},
        {'type': Tokens.RIGHT_BRACKET},
        {'type': Tokens.EOF}
    ]
    assert_token_list_equal(tokens, expected)
    # range with step
    text = '{par1} [1:10:2]'
    tokens = tokenize(text)
    expected = [
        {'type': Tokens.LEFT_BRACE},
        {'type': Tokens.IDENTIFIER, 'value': 'par1'},
        {'type': Tokens.RIGHT_BRACE},
        {'type': Tokens.LEFT_BRACKET},
        {'type': Tokens.INTEGER, 'value': '1'},
        {'type': Tokens.COLON},
        {'type': Tokens.INTEGER, 'value': '10'},
        {'type': Tokens.COLON},
        {'type': Tokens.INTEGER, 'value': '2'},
        {'type': Tokens.RIGHT_BRACKET},
        {'type': Tokens.EOF}
    ]
    assert_token_list_equal(tokens, expected)
    # range with step and default
    text = '{ par1 } [1 : 10 : 2 => 5]'
    tokens = tokenize(text)
    expected = [
        {'type': Tokens.LEFT_BRACE},
        {'type': Tokens.IDENTIFIER, 'value': 'par1'},
        {'type': Tokens.RIGHT_BRACE},
        {'type': Tokens.LEFT_BRACKET},
        {'type': Tokens.INTEGER, 'value': '1'},
        {'type': Tokens.COLON},
        {'type': Tokens.INTEGER, 'value': '10'},
        {'type': Tokens.COLON},
        {'type': Tokens.INTEGER, 'value': '2'},
        {'type': Tokens.DEFAULT_MARKER},
        {'type': Tokens.INTEGER, 'value': '5'},
        {'type': Tokens.RIGHT_BRACKET},
        {'type': Tokens.EOF}
    ]
    assert_token_list_equal(tokens, expected)


def test_free_text_after_param():
    text = '{ par1 } Some free text (wow, [snafu])'
    tokens = tokenize(text)
    expected = [
        {'type': Tokens.LEFT_BRACE},
        {'type': Tokens.IDENTIFIER, 'value': 'par1'},
        {'type': Tokens.RIGHT_BRACE},
        {'type': Tokens.TEXT},
        {'type': Tokens.EOF}
    ]
    assert_token_list_equal(tokens, expected)

    text = '''{ par1 } Some free text (wow, [snafu])
        {par2} (hint) Other text
        {par3} (hint) ["foo"] Yet another doctext
    '''
    tokens = tokenize(text)
    expected = [
        {'type': Tokens.LEFT_BRACE},
        {'type': Tokens.IDENTIFIER, 'value': 'par1'},
        {'type': Tokens.RIGHT_BRACE},
        {'type': Tokens.TEXT},
        {'type': Tokens.LEFT_BRACE},
        {'type': Tokens.IDENTIFIER, 'value': 'par2'},
        {'type': Tokens.RIGHT_BRACE},
        {'type': Tokens.LEFT_PAREN},
        {'type': Tokens.IDENTIFIER, 'value': 'hint'},
        {'type': Tokens.RIGHT_PAREN},
        {'type': Tokens.TEXT},
        {'type': Tokens.LEFT_BRACE},
        {'type': Tokens.IDENTIFIER, 'value': 'par3'},
        {'type': Tokens.RIGHT_BRACE},
        {'type': Tokens.LEFT_PAREN},
        {'type': Tokens.IDENTIFIER, 'value': 'hint'},
        {'type': Tokens.RIGHT_PAREN},
        {'type': Tokens.LEFT_BRACKET},
        {'type': Tokens.STRING, 'value': 'foo'},
        {'type': Tokens.RIGHT_BRACKET},
        {'type': Tokens.TEXT},
        {'type': Tokens.EOF}
    ]
    assert_token_list_equal(tokens, expected)


def test_code_block():
    text = '''
```
import foo, bar
params['foo'] = '{bar}'
```'''
    tokens = tokenize(text)
    expected = [
        {'type': Tokens.TEXT},
        {'type': Tokens.CODE_FENCE},
        {'type': Tokens.TEXT},
        {'type': Tokens.CODE_FENCE},
        {'type': Tokens.EOF}
    ]
    assert_token_list_equal(tokens, expected)

    text = '''{par1} Some text
```
import foo, bar
params['foo'] = '{bar}'
```
{par2} Other text.
    '''
    tokens = tokenize(text)
    expected = [
        {'type': Tokens.LEFT_BRACE},
        {'type': Tokens.IDENTIFIER, 'value': 'par1'},
        {'type': Tokens.RIGHT_BRACE},
        {'type': Tokens.TEXT},
        {'type': Tokens.CODE_FENCE},
        {'type': Tokens.TEXT},
        {'type': Tokens.CODE_FENCE},
        {'type': Tokens.TEXT},
        {'type': Tokens.LEFT_BRACE},
        {'type': Tokens.IDENTIFIER, 'value': 'par2'},
        {'type': Tokens.RIGHT_BRACE},
        {'type': Tokens.TEXT},
        {'type': Tokens.EOF}
    ]
    assert_token_list_equal(tokens, expected)


def test_complex_code_block():
    text = r'''```
foo = "bar\"baz"
params['foo'] = "{bar}"
bar = 'a\'b\'c'
baz = """
"
```
codemarks in strings should be skipped !
"""
```'''
    tokens = tokenize(text)
    expected = [
        {'type': Tokens.CODE_FENCE},
        {'type': Tokens.TEXT},
        {'type': Tokens.CODE_FENCE},
        {'type': Tokens.EOF}
    ]
    assert_token_list_equal(tokens, expected)
