from decimal import Decimal
import pytest

from clisnips.exceptions import ParseError
from clisnips.syntax.documentation import parse
from clisnips.syntax.documentation.executor import Executor
from clisnips.syntax.documentation.nodes import CodeBlock, Parameter, ValueList, ValueRange


def test_parse_empty_string():
    doc = parse('')
    assert doc.header == ''
    assert list(doc.parameters.values()) == []


def test_parse_free_text():
    text = """
        This is the global description of the command.
        It's all text until a {parameter} is seen.
        A {param} must start a line (possibly indented).
    """
    doc = parse(text)
    assert doc.header == text
    assert list(doc.parameters.values()) == []


def test_parse_parameter():
    text = 'Global doc\n{par1} (file) Param doc'
    doc = parse(text)
    assert doc.header == 'Global doc\n'
    assert 'par1' in doc.parameters
    param = doc.parameters['par1']
    assert isinstance(param, Parameter)
    assert param.name == 'par1'
    assert param.type_hint == 'file'
    assert param.text == 'Param doc'


def test_parse_flag():
    text = 'Global doc\n{--flag} Some flag\n{-f} Other flag'
    doc = parse(text)
    assert doc.header == 'Global doc\n'
    #
    assert '--flag' in doc.parameters
    param = doc.parameters['--flag']
    assert isinstance(param, Parameter)
    assert param.name == '--flag'
    assert param.type_hint == 'flag'
    assert param.text == 'Some flag\n'
    #
    assert '-f' in doc.parameters
    param = doc.parameters['-f']
    assert isinstance(param, Parameter)
    assert param.name == '-f'
    assert param.type_hint == 'flag'
    assert param.text == 'Other flag'


def test_automatic_numbering():
    text = '{} foo\n{} bar'
    doc = parse(text)
    assert len(doc.parameters) == 2
    assert '0' in doc.parameters
    assert '1' in doc.parameters
    #
    text = '{} foo\n{1} bar'
    with pytest.raises(ParseError, match='field numbering'):
        doc = parse(text)
    #
    text = '{1} foo\n{} bar'
    with pytest.raises(ParseError, match='field numbering'):
        doc = parse(text)


def test_parse_value_list():
    # digit list
    text = '{par1} [1, =>-2, 0.3]'
    doc = parse(text)
    assert 'par1' in doc.parameters
    param = doc.parameters['par1']
    assert isinstance(param, Parameter)
    assert param.name == 'par1'
    assert param.type_hint is None
    assert param.text == ''
    values = param.value_hint
    assert isinstance(values, ValueList)
    assert values.values == [Decimal('1'), Decimal('-2'), Decimal('0.3')]
    assert values.default == 1

    # string list
    text = '{par1} ["foo", =>"bar", "baz"]'
    doc = parse(text)
    assert 'par1' in doc.parameters
    param = doc.parameters['par1']
    assert isinstance(param, Parameter)
    assert param.name == 'par1'
    assert param.type_hint is None
    assert param.text == ''
    values = param.value_hint
    assert isinstance(values, ValueList)
    assert values.values == ['foo', 'bar', 'baz']
    assert values.default == 1


def test_parse_value_range():
    text = '{par1} [1:10:2=>5]'
    doc = parse(text)
    assert 'par1' in doc.parameters
    param = doc.parameters['par1']
    assert isinstance(param, Parameter)
    assert param.name == 'par1'
    assert param.type_hint is None
    assert param.text == ''
    hint = param.value_hint
    assert isinstance(hint, ValueRange)
    assert hint.start == 1
    assert hint.end == 10
    assert hint.step == 2
    assert hint.default == 5
    # default step
    text = '{par1} [1:10=>5]'
    doc = parse(text)
    assert 'par1' in doc.parameters
    param = doc.parameters['par1']
    hint = param.value_hint
    assert isinstance(hint, ValueRange)
    assert hint.step == 1
    assert hint.default == 5
    # default step
    text = '{par1} [0.1:0.25]'
    doc = parse(text)
    assert 'par1' in doc.parameters
    param = doc.parameters['par1']
    hint = param.value_hint
    assert isinstance(hint, ValueRange)
    assert hint.step == Decimal('0.01')
    # default step
    text = '{par1} [1:1.255]'
    doc = parse(text)
    assert 'par1' in doc.parameters
    param = doc.parameters['par1']
    hint = param.value_hint
    assert isinstance(hint, ValueRange)
    assert hint.step == Decimal('0.001')


def test_parse_code_block():
    code_str = """
import os.path
if fields['infile'] and not fields['outfile']:
    path, ext = os.path.splitext(fields['infile'])
    fields['outfile'] = path + '.mp4'
"""
    text = (
        """
{infile} (path) The input file
{outfile} (path) The output file
```%s```
    """
        % code_str
    )
    doc = parse(text)
    #
    assert 'infile' in doc.parameters
    param = doc.parameters['infile']
    assert isinstance(param, Parameter)
    assert param.name == 'infile'
    assert param.type_hint == 'path'
    assert param.text == 'The input file\n'
    #
    assert 'outfile' in doc.parameters
    param = doc.parameters['outfile']
    assert isinstance(param, Parameter)
    assert param.name == 'outfile'
    assert param.type_hint == 'path'
    assert param.text == 'The output file\n'
    #
    assert len(doc.code_blocks) == 1
    code = doc.code_blocks[0]
    assert isinstance(code, CodeBlock)
    assert code.code == code_str
    # execute code
    ctx = {
        'fields': {
            'infile': '/foo/bar.wav',
            'outfile': '',
        },
    }
    result = Executor(doc).execute(ctx)
    assert result['fields']['outfile'] == '/foo/bar.mp4'


@pytest.mark.parametrize(
    ('text', 'message'),
    (
        ('{$$$}', 'Unexpected token'),
        ('{} ($$$)', 'Unexpected token'),
        ('{} (string) [$$$]', 'Unexpected token'),
        ('{}\n{1}', 'Cannot switch from automatic to manual field numbering'),
        ('{1}\n{}', 'Cannot switch from manual to automatic field numbering'),
        ('{-f} (string)', 'flag cannot have a type hint'),
        ('{-f} ["foo", "bar"]', 'flag cannot have a value hint'),
        (r'```x = <error!>```', 'Syntax error'),
    ),
)
def test_parse_errors(text: str, message: str):
    with pytest.raises(ParseError, match=message):
        _ = parse(text)
