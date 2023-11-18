from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from string import Formatter as _StringFormatter
from typing import Any


@dataclass(slots=True, frozen=True)
class Text:
    value: str
    start: int
    end: int

    def __str__(self):
        return self.value


@dataclass(slots=True, frozen=True)
class Field:
    name: str
    start: int
    end: int
    format_spec: str | None = ''
    conversion: str | None = None

    def __str__(self):
        conv = f'!{self.conversion}' if self.conversion else ''
        spec = f':{self.format_spec}' if self.format_spec else ''
        return f'{{{self.name}{conv}{spec}}}'


class _CommandFormatter(_StringFormatter):
    def get_value(self, key: int | str, args: Sequence[Any], kwargs: Mapping[str, Any]) -> Any:
        # we override so that we don't have to convert numeric fields
        # to integers and split args and kwargs
        return kwargs[str(key)]


class CommandTemplate:

    def __init__(self, raw: str, nodes: list[Text | Field]):
        self.raw = raw
        self.nodes = nodes
        self._formatter = _CommandFormatter()

    @property
    def text(self) -> str:
        return ''.join(n.value for n in self.nodes if isinstance(n, Text))

    @property
    def fields(self) -> Iterable[Field]:
        return (n for n in self.nodes if isinstance(n, Field))

    def has_fields(self) -> bool:
        return any(self.fields)

    @property
    def field_names(self) -> Iterable[str]:
        return (f.name for f in self.fields)

    def render(self, context: Mapping[str, str]) -> str:
        return ''.join(v for _, v in self.apply(context))

    def apply(self, context: Mapping[str, str]) -> Iterable[tuple[bool, str]]:
        for node in self.nodes:
            if isinstance(node, Text):
                yield (False, node.value)
                continue
            value, _ = self._formatter.get_field(node.name, (), context)
            if node.conversion:
                value = self._formatter.convert_field(value, node.conversion)
            if node.format_spec:
                value = self._formatter.format_field(value, node.format_spec)
            yield (True, value)

    def __eq__(self, other):
        return other.raw == self.raw and other.nodes == self.nodes

    def __str__(self):
        return ''.join(str(n) for n in self.nodes)
