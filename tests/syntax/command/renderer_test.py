import pytest
from clisnips.syntax.command.err import InterpolationError, InterpolationErrorGroup, InvalidContext

from clisnips.syntax.command.parser import parse
from clisnips.syntax.command.renderer import Renderer

TEXT = 'text'
FIELD = 'field'


@pytest.mark.parametrize(
    ('raw', 'context', 'expected_str', 'expected_markup'),
    (
        (
            'foo',
            {'bar': 'baz'},
            'foo',
            [(TEXT, 'foo')],
        ),
        (
            'foo {bar}',
            {'bar': 'baz'},
            'foo baz',
            [(TEXT, 'foo '), (FIELD, 'baz')],
        ),
        (
            'foo {bar!r}',
            {'bar': 'baz'},
            "foo 'baz'",
            [(TEXT, 'foo '), (FIELD, "'baz'")],
        ),
        (
            'foo {poo:🤟^5}',
            {'poo': '💩'},
            'foo 🤟🤟💩🤟🤟',
            [(TEXT, 'foo '), (FIELD, '🤟🤟💩🤟🤟')],
        ),
        (
            'x={v:.3f}',
            {'v': 1 / 3},
            'x=0.333',
            [(TEXT, 'x='), (FIELD, '0.333')],
        ),
        (
            '0x{v:X}',
            {'v': 3735928559},
            '0xDEADBEEF',
            [(TEXT, '0x'), (FIELD, 'DEADBEEF')],
        ),
        (
            'i haz {} {:.2f} fields',
            {
                '0': 'zaroo',
                '1': 1 / 3,
                'foo': {'bar': 42},
            },
            'i haz zaroo 0.33 fields',
            [
                (TEXT, 'i haz '),
                (FIELD, 'zaroo'),
                (TEXT, ' '),
                (FIELD, '0.33'),
                (TEXT, ' fields'),
            ],
        ),
    ),
)
def test_apply(raw, context, expected_str, expected_markup):
    tpl = parse(raw)
    renderer = Renderer()
    result = renderer.render_str(tpl, context)
    assert result == expected_str
    result = renderer.render_markup(tpl, context)
    assert result == expected_markup


@pytest.mark.parametrize(
    ('raw', 'context'),
    (
        (
            '{v:X}',
            {'v': 'nope'},
        ),
    ),
)
def test_interpolation_errors(raw, context):
    tpl = parse(raw)
    with pytest.raises(InterpolationErrorGroup) as err:
        _ = Renderer().render_str(tpl, context)
    assert isinstance(err.value.exceptions[0], InterpolationError)


def test_context_accepts_only_string_keys():
    tpl = parse('{0:X}')
    renderer = Renderer()
    result = renderer.render_str(tpl, {'0': 666})
    assert result == '29A'
    with pytest.raises(InterpolationErrorGroup) as err:
        _ = renderer.render_str(tpl, {0: 666})  # type: ignore (we're asserting that)
    assert isinstance(err.value.exceptions[0], InvalidContext)
