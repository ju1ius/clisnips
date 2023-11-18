import pytest

from clisnips.exceptions import ParseError
from clisnips.syntax.command.parser import parse
from clisnips.syntax.command.nodes import Field, Text


def test_no_replacement_fields():
    raw = 'i haz no fields'
    cmd = parse(raw)
    expected = [Text(raw, 0, 15)]
    assert cmd.nodes == expected


def test_simple_replacement_field():
    raw = 'i haz {one} field'
    cmd = parse(raw)
    expected = [
        Text('i haz ', 0, 6),
        Field('one', 6, 11),
        Text(' field', 11, 17)
    ]
    assert cmd.nodes == expected


def test_it_supports_flags():
    raw = 'i haz {-1} {--two} flags'
    cmd = parse(raw)
    expected = [
        Text('i haz ', 0, 6),
        Field('-1', 6, 10),
        Text(' ', 10, 11),
        Field('--two', 11, 18),
        Text(' flags', 18, 24)
    ]
    assert cmd.nodes == expected


def test_automatic_numbering():
    raw = 'i haz {} {} flags'
    cmd = parse(raw)
    expected = [
        Text('i haz ', 0, 6),
        Field('0', 6, 8),
        Text(' ', 8, 9),
        Field('1', 9, 11),
        Text(' flags', 11, 17)
    ]
    assert cmd.nodes == expected


def test_conversion():
    raw = 'i haz {one!r} field'
    cmd = parse(raw)
    expected = [
        Text('i haz ', 0, 6),
        Field('one', 6, 13, '', 'r'),
        Text(' field', 13, 19)
    ]
    assert cmd.nodes == expected


def test_format_spec():
    raw = 'i haz {0:.1f} field'
    cmd = parse(raw)
    expected = [
        Text('i haz ', 0, 6),
        Field('0', 6, 13, '.1f', None),
        Text(' field', 13, 19)
    ]
    assert cmd.nodes == expected


def test_it_cannot_switch_from_auto_to_manual_numbering():
    raw = 'i haz {1} {} fields'
    with pytest.raises(ParseError, match='field numbering'):
        _ = parse(raw)


def test_field_inside_format_spec():
    raw = 'i haz {one:%s {2}} field'
    with pytest.raises(ParseError, match='not supported'):
        _ = parse(raw)


def test_field_getitem():
    raw = 'i haz {foo[bar]} field'
    with pytest.raises(ParseError):
        _ = parse(raw)


def test_field_getattr():
    raw = 'i haz {foo.bar} field'
    with pytest.raises(ParseError):
        _ = parse(raw)


def test_command_apply():
    raw = 'i haz {} {:.2f} fields'
    cmd = parse(raw)
    output = list(cmd.apply({
        '0': 'zaroo',
        '1': 1 / 3, # type: ignore (we're testing if it handles other types correctly)
        'foo': {'bar': 42}
    }))
    expected = [
        (False, 'i haz '),
        (True, 'zaroo'),
        (False, ' '),
        (True, '0.33'),
        (False, ' fields'),
    ]
    assert expected == output

