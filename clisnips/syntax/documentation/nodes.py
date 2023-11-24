from __future__ import annotations
from dataclasses import dataclass

from decimal import Decimal

from clisnips.utils.number import clamp_to_range, get_default_range_step


@dataclass(slots=True, frozen=True)
class Documentation:
    header: str
    parameters: dict[str, Parameter]
    code_blocks: list[CodeBlock]

    def __str__(self):
        code = '\n'.join(str(c) for c in self.code_blocks)
        params = '\n'.join(str(p) for p in self.parameters.values())
        return f'{self.header!s}{params}{code}'

    def __repr__(self):
        return str(self)


@dataclass(slots=True)
class Parameter:
    name: str
    type_hint: str | None = None
    value_hint: ValueList | ValueRange | None = None
    text: str = ''

    def __str__(self):
        return f'{{{self.name}}} ({self.type_hint}) {self.value_hint} {self.text!r}'

    def __repr__(self):
        return str(self)


class ValueRange:
    def __init__(
        self,
        start: Decimal,
        end: Decimal,
        step: Decimal | None = None,
        default: Decimal | None = None,
    ):
        self.start = start
        self.end = end
        self.step = get_default_range_step(start, end) if step is None else step
        if default is None:
            default = start
        self.default = clamp_to_range(default, start, end)

    def __str__(self):
        return '[%s..%s:%s*%s]' % (self.start, self.end, self.step, self.default)  # noqa: UP031 (this is more readable)

    def __repr__(self):
        return str(self)


Value = str | Decimal


@dataclass(slots=True, frozen=True)
class ValueList:
    values: list[Value]
    default: int = 0

    def get_default_value(self) -> Value:
        return self.values[self.default]

    def __len__(self) -> int:
        return len(self.values)

    def __str__(self) -> str:
        values: list[str] = []
        for i, value in enumerate(self.values):
            value = repr(value)
            if i == self.default:
                value = f'=>{value}'
            values.append(value)
        return '[%s]' % ', '.join(values)

    def __repr__(self):
        return str(self)


@dataclass(slots=True, frozen=True)
class CodeBlock:
    code: str

    def __str__(self):
        return f'```\n{self.code}\n```'

    def __repr__(self):
        return str(self)
