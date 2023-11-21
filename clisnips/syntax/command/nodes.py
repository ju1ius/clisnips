from collections.abc import Iterable
from dataclasses import dataclass
from typing import TypeAlias


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


Node: TypeAlias = Field | Text


class CommandTemplate:
    def __init__(self, raw: str, nodes: list[Node]):
        self.raw = raw
        self.nodes = nodes

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

    def __eq__(self, other):
        return other.raw == self.raw and other.nodes == self.nodes

    def __str__(self):
        return ''.join(str(n) for n in self.nodes)
