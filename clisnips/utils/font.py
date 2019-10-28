from typing import Union

from gi.repository import Pango

FontSpec = Union[Pango.FontDescription, str]


def parse_font(spec: FontSpec) -> Pango.FontDescription:
    if isinstance(spec, Pango.FontDescription):
        return spec
    return Pango.FontDescription(spec)
