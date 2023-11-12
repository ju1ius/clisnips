

palette = [
    # (name, foreground, background, mono=None, foreground_high=None, background_high=None)
    ('default', 'light gray', 'black'),
    ('view:default', 'light gray', 'black'),
    ('search-entry:caption', 'dark cyan', 'black'),

    # Help screen
    ('help:key', 'dark cyan', 'black'),

    # Buttons
    ('button:suggested', 'dark cyan,bold', 'black'),
    ('button:destructive', 'dark red,bold', 'black'),

    ('error', 'white', 'dark red'),
    ('warning', 'black', 'brown'),
    ('info', 'white', 'dark blue', '', 'h186', 'g20'),

    # snippets list
    ('snippets-list:focused', 'light gray', 'dark gray', 'standout'),
    ('snippets-list:cmd', 'dark green', 'black'),
    ('snippets-list:cmd:focused', 'dark green', 'dark gray', 'standout'),
    ('snippets-list:title', 'light gray,italics', 'black'),
    ('snippets-list:title:focused', 'light gray,italics', 'dark gray', 'standout'),
    ('snippets-list:tag', 'brown', 'black'),
    ('snippets-list:tag:focused', 'brown', 'dark gray', 'standout'),

    ('path-completion:file', 'light gray', 'default'),
    ('path-completion:directory', 'dark blue', 'default'),
    ('path-completion:symlink-directory', 'dark cyan', 'default'),
    ('path-completion:symlink-file', 'brown', 'default'),

    # Syntax highlighting
    ('syn:cmd:default', 'dark green', 'black'),
    ('syn:cmd:punctuation', 'light gray', 'black'),
    ('syn:cmd:field-marker', 'dark magenta', 'black'),
    ('syn:cmd:field-name', 'dark magenta', 'black'),
    ('syn:cmd:field-conversion', 'dark cyan', 'black'),
    ('syn:cmd:field-format', 'dark cyan', 'black'),

    ('syn:doc:default', 'light gray', 'black'),
    ('syn:doc:parameter', 'dark magenta', 'black'),
    ('syn:doc:type-hint', 'dark cyan', 'black'),
    ('syn:doc:value-hint', 'brown', 'black'),
    ('syn:doc:value-hint:default', 'light cyan', 'black'),
    ('syn:doc:string', 'dark green', 'black'),
    ('syn:doc:number', 'yellow', 'black'),
    ('syn:doc:code-fence', 'dark red', 'black'),
    #
    ('syn:py:default', 'light gray', 'black'),
    ('syn:py:name', 'light gray', 'black'),
    ('syn:py:comment', 'dark gray', 'black'),
    ('syn:py:keyword', 'dark magenta', 'black'),
    ('syn:py:class', 'brown', 'black'),
    ('syn:py:decorator', 'brown', 'black'),
    ('syn:py:string', 'dark green', 'black'),
    ('syn:py:string:escape', 'light cyan', 'black'),
    ('syn:py:string:interp', 'light gray', 'black'),
    ('syn:py:function', 'dark cyan', 'black'),
    ('syn:py:number', 'yellow', 'black'),

    # Diffs
    ('diff:insert', 'dark magenta', 'black', 'standout'),
    ('diff:delete', 'light gray,bold', 'dark red'),
]
