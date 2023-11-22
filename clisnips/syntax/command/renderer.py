import shlex
from collections.abc import Iterable, Mapping, Sequence
from decimal import Decimal
from string import Formatter as _StringFormatter
from typing import Any, TypeAlias

from clisnips.tui.urwid_types import TextMarkup
from clisnips.utils.number import is_integer_decimal

from .err import InterpolationError, InterpolationErrorGroup, InvalidContext
from .nodes import CommandTemplate, Field, Node, Text

Context: TypeAlias = Mapping[str, object]


class Renderer:
    def __init__(self) -> None:
        self._formatter = _CommandFormatter()

    def render_str(self, tpl: CommandTemplate, ctx: Context) -> str:
        return ''.join(v for _, v in self.interpolate(tpl, ctx))

    def render_markup(self, tpl: CommandTemplate, ctx: Context) -> TextMarkup:
        return self.try_render_markup(tpl, ctx)[0]

    def try_render_markup(self, tpl: CommandTemplate, ctx: Context) -> tuple[TextMarkup, list[InterpolationError]]:
        markup: TextMarkup = []
        errors: list[InterpolationError] = []
        for item in self.try_interpolate(tpl, ctx):
            match item:
                case InterpolationError():
                    markup.append(('error', f'<error({item.field.name})>'))
                    errors.append(item)
                case (_, ''):
                    continue
                case (Text(), value):
                    markup.append(('text', value))
                case (Field(), value):
                    markup.append(('field', value))
        return markup, errors

    def interpolate(self, tpl: CommandTemplate, ctx: Context) -> Iterable[tuple[Node, str]]:
        errors: list[InterpolationError] = []
        for item in self.try_interpolate(tpl, ctx):
            if isinstance(item, InterpolationError):
                errors.append(item)
            else:
                yield item
        if errors:
            raise InterpolationErrorGroup('Interpolation errors', errors)

    def try_interpolate(self, tpl: CommandTemplate, ctx: Context) -> Iterable[tuple[Node, str] | InterpolationError]:
        for node in tpl.nodes:
            if isinstance(node, Text):
                yield (node, node.value)
                continue
            try:
                value, _ = self._formatter.get_field(node.name, (), ctx)
            except KeyError as err:
                yield InvalidContext(f'Missing context key: {err}', node)
                continue
            except Exception as err:
                yield InvalidContext(f'Invalid context: {err}', node)
                continue
            if node.conversion:
                try:
                    value = self._formatter.convert_field(value, node.conversion)
                except ValueError as err:
                    yield InterpolationError(str(err), node)
                    continue
            if node.format_spec:
                try:
                    value = self._formatter.format_field(value, node.format_spec)
                except ValueError as err:
                    yield InterpolationError(str(err), node)
                    continue
            yield (node, value)


class _CommandFormatter(_StringFormatter):
    def get_value(self, key: int | str, args: Sequence[Any], kwargs: Mapping[str, Any]) -> Any:
        # we override so that we don't have to convert numeric fields
        # to integers and split args and kwargs
        return kwargs[str(key)]

    def convert_field(self, value: Any, conversion: str) -> Any:
        match conversion:
            case 'q':
                return shlex.quote(str(value))
            case _:
                return super().convert_field(value, conversion)

    def format_field(self, value: Any, format_spec: str) -> Any:
        try:
            return super().format_field(value, format_spec)
        except:
            # Allow integer-specific format specs (i.e. {:X}) for decimals
            if isinstance(value, Decimal) and is_integer_decimal(value):
                return super().format_field(int(value), format_spec)
            raise
