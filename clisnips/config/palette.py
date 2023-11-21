from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, create_model

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


class PaletteEntry(BaseModel):
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


_palette_field_defs = {
    k: (
        PaletteEntry | str,
        Field(default=v if isinstance(v, str) else PaletteEntry(**v)),
    )
    for k, v in default_palette.items()
}  # fmt: skip

Palette = create_model('Palette', **_palette_field_defs)  # type: ignore
