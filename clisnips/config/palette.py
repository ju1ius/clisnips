from __future__ import annotations

from typing import NotRequired
from typing_extensions import TypedDict


class PaletteEntry(TypedDict):
    fg: str
    bg: str
    mono: NotRequired[str|None]
    fg_hi: NotRequired[str|None]
    bg_hi: NotRequired[str|None]


default_palette = {
    'default': {'fg': 'light gray', 'bg': 'black'},
    'info': {'fg': 'white', 'bg': 'dark blue', 'mono': None, 'fg_hi': 'h186', 'bg_hi': 'g20'},
    'warning': {'fg': 'black', 'bg': 'brown'},
    'error': {'fg': 'white', 'bg': 'dark red'},
    'button:suggested': {'fg': 'dark cyan,bold', 'bg': 'black'},
    'button:destructive': {'fg': 'dark red,bold', 'bg': 'black'},

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

    # diffs
    'diff:insert': {'fg': 'dark magenta', 'bg': 'black', 'mono': 'standout'},
    'diff:delete': {'fg': 'light gray,bold', 'bg': 'dark red'},
}


Palette = TypedDict(
    'Palette',
    {k: PaletteEntry | str for k in default_palette.keys()},
    total=False,
)
