from __future__ import annotations
from typing import Any, NotRequired, TypeAlias, cast
from typing_extensions import TypedDict

from pydantic import BaseModel, ConfigDict, Field, create_model

from clisnips.exceptions import InvalidConfiguration

default_palette = {
    'default': {'fg': 'light gray', 'bg': 'black'},
    'info': {'fg': 'dark blue', 'bg': 'default'},
    'success': {'fg': 'dark green', 'bg': 'default'},
    'warning': {'fg': 'brown', 'bg': 'default'},
    'error': {'fg': 'dark red', 'bg': 'default'},
    'disabled': {'fg': 'dark gray,bold', 'bg': 'black'},

    'action:suggested': {'fg': 'dark cyan,bold', 'bg': 'black'},
    'action:destructive': {'fg': 'dark red,bold', 'bg': 'black'},
    'action:disabled': 'disabled',

    'choice:inactive': 'default',
    'choice:active': {'fg': 'dark cyan', 'bg': 'black'},
    'choice:disabled': 'disabled',

    # key binding
    'help:key': {'fg': 'dark cyan', 'bg': 'black'},

    # views / components
    'view:default': {'fg': 'light gray', 'bg': 'black'},
    'search-entry:caption': {'fg': 'dark cyan', 'bg': 'black'},
    'snippets-list:focused': {'fg': 'light gray', 'bg': 'dark gray', 'mono': 'standout'},
    'snippets-list:cmd': {'fg': 'dark green', 'bg': 'black'},
    'snippets-list:cmd:focused': {'fg': 'dark green', 'bg': 'dark gray', 'mono': 'standout'},
    'snippets-list:title': {'fg': 'light gray,italics', 'bg': 'black'},
    'snippets-list:title:focused': {'fg': 'light gray,italics', 'bg': 'dark gray', 'mono': 'standout'},
    'snippets-list:tag': {'fg': 'brown', 'bg': 'black'},
    'snippets-list:tag:focused': {'fg': 'brown', 'bg': 'dark gray', 'mono': 'standout'},

    # widgets
    'path-completion:file': {'fg': 'light gray', 'bg': 'default'},
    'path-completion:directory': {'fg': 'dark blue', 'bg': 'default'},
    'path-completion:symlink-directory': {'fg': 'dark cyan', 'bg': 'default'},
    'path-completion:symlink-file': {'fg': 'brown', 'bg': 'default'},

    # syntax highlighting
    'syn:cmd:default': {'fg': 'dark green', 'bg': 'black'},
    'syn:cmd:punctuation': {'fg': 'light gray', 'bg': 'black'},
    'syn:cmd:field-marker': {'fg': 'dark magenta', 'bg': 'black'},
    'syn:cmd:field-name': {'fg': 'dark magenta', 'bg': 'black'},
    'syn:cmd:field-conversion': {'fg': 'dark cyan', 'bg': 'black'},
    'syn:cmd:field-format': {'fg': 'dark cyan', 'bg': 'black'},

    'syn:doc:default': {'fg': 'light gray', 'bg': 'black'},
    'syn:doc:parameter': {'fg': 'dark magenta', 'bg': 'black'},
    'syn:doc:type-hint': {'fg': 'dark cyan', 'bg': 'black'},
    'syn:doc:value-hint': {'fg': 'brown', 'bg': 'black'},
    'syn:doc:value-hint:default': {'fg': 'light cyan', 'bg': 'black'},
    'syn:doc:string': {'fg': 'dark green', 'bg': 'black'},
    'syn:doc:number': {'fg': 'yellow', 'bg': 'black'},
    'syn:doc:code-fence': {'fg': 'dark red', 'bg': 'black'},

    'syn:py:default': {'fg': 'light gray', 'bg': 'black'},
    'syn:py:name': {'fg': 'light gray', 'bg': 'black'},
    'syn:py:comment': {'fg': 'dark gray', 'bg': 'black'},
    'syn:py:keyword': {'fg': 'dark magenta', 'bg': 'black'},
    'syn:py:class': {'fg': 'brown', 'bg': 'black'},
    'syn:py:decorator': {'fg': 'brown', 'bg': 'black'},
    'syn:py:string': {'fg': 'dark green', 'bg': 'black'},
    'syn:py:string:escape': {'fg': 'light cyan', 'bg': 'black'},
    'syn:py:string:interp': {'fg': 'light gray', 'bg': 'black'},
    'syn:py:function': {'fg': 'dark cyan', 'bg': 'black'},
    'syn:py:number': {'fg': 'yellow', 'bg': 'black'},
}  # fmt: skip


class PaletteEntry(TypedDict):
    fg: str
    bg: str
    mono: NotRequired[str | None]
    fg_hi: NotRequired[str | None]
    bg_hi: NotRequired[str | None]


Palette: TypeAlias = dict[str, PaletteEntry]


class PaletteEntryModel(BaseModel):
    model_config = ConfigDict(
        title='An Urwid palette entry',
        json_schema_extra={
            'description': (
                'See available color values at: '
                'https://urwid.org/manual/displayattributes.html#foreground-and-background-settings'
            ),
        },
    )

    fg: str = Field(title='Foreground color in 16-color mode')
    bg: str = Field(title='Background color in 16-color mode')
    mono: str | None = Field(title='Color in monochrome mode', default=None)
    fg_hi: str | None = Field(title='Foreground color in high-color mode', default=None)
    bg_hi: str | None = Field(title='Background color in high-color mode', default=None)


_palette_model_fields = {
    k: (
        PaletteEntryModel | str,
        Field(default=v if isinstance(v, str) else PaletteEntryModel(**v)),
    )
    for k, v in default_palette.items()
}  # fmt: skip


class _BasePalette(BaseModel):
    def resolved(self) -> Palette:
        palette = self.model_dump()
        for name, entry in palette.items():
            if not isinstance(entry, dict):
                palette[name] = _revolve_entry(entry, palette)
        return palette


PaletteModel = cast(
    type[_BasePalette],
    create_model(
        'PaletteModel',
        __base__=_BasePalette,
        **_palette_model_fields,  # type: ignore
    ),
)


def _revolve_entry(ref: Any, palette: dict[str, PaletteEntry | str]) -> PaletteEntry:
    seen = set()
    while True:
        if ref in seen:
            raise InvalidConfiguration(f'Circular color reference: {ref!r}')
        try:
            color = palette[ref]
        except KeyError:
            raise InvalidConfiguration(f'Invalid color reference: {ref!r}') from None
        if isinstance(color, dict):
            return color
        seen.add(ref)
        ref = color
