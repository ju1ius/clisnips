from string import Formatter as _StringFormatter
from typing import Dict, List, Optional, Tuple, Union


class Text:
    __slots__ = ('text', 'start', 'end')

    def __init__(self, text: str, start: int, end: int):
        self.text = text
        self.start = start
        self.end = end

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and other.start == self.start
                and other.text == self.text)

    def __repr__(self):
        return f'<Text @[{self.start},{self.end}] {self.text!r}>'

    def __str__(self):
        return self.text


class Field:
    __slots__ = ('name', 'start', 'end', 'format_spec', 'conversion')

    def __init__(self, name: str, start: int, end: int,
                 format_spec: Optional[str] = '', conversion: Optional[str] = None):
        self.name = name
        self.start = start
        self.end = end
        self.format_spec = format_spec
        self.conversion = conversion

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and other.start == self.start
                and other.name == self.name
                and other.format_spec == self.format_spec
                and other.conversion == self.conversion)

    def __repr__(self):
        return f'<Field @[{self.start},{self.end}] {self!s}>'

    def __str__(self):
        conv = f'!{self.conversion}' if self.conversion else ''
        spec = f':{self.format_spec}' if self.format_spec else ''
        return f'{{{self.name}{conv}{spec}}}'


class _CommandFormatter(_StringFormatter):

    def get_value(self, key, args, kwargs):
        # we override so that we don't have to convert numeric fields
        # to integers and split args and kwargs
        return kwargs[str(key)]


class CommandTemplate:

    def __init__(self, raw: str, nodes: List[Union[Text, Field]]):
        self.raw = raw
        self.nodes = nodes
        self._formatter = _CommandFormatter()

    @property
    def text(self) -> str:
        return ''.join(n.text for n in self.nodes if isinstance(n, Text))

    @property
    def replacement_fields(self) -> List[Field]:
        return [n for n in self.nodes if isinstance(n, Field)]

    @property
    def field_names(self) -> List[str]:
        return [n.name for n in self.nodes if isinstance(n, Field)]

    def render(self, context: Dict[str, str]) -> str:
        return ''.join(v for _, v in self.apply(context))

    def apply(self, context: Dict[str, str]) -> List[Tuple[bool, str]]:
        output = []
        for node in self.nodes:
            if isinstance(node, Text):
                output.append((False, node.text))
                continue
            value, _ = self._formatter.get_field(node.name, (), context)
            value = self._formatter.convert_field(value, node.conversion)
            value = self._formatter.format_field(value, node.format_spec)
            output.append((True, value))
        return output

    def __eq__(self, other):
        return other.raw == self.raw and other.nodes == self.nodes

    def __str__(self):
        return ''.join(str(n) for n in self.nodes)
