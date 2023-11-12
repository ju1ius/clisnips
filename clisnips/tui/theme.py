

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
    ('cmd:default', 'dark green', 'black'),
    ('cmd:punctuation', 'light gray', 'black'),
    ('cmd:field-marker', 'dark magenta', 'black'),
    ('cmd:field-name', 'dark magenta', 'black'),
    ('cmd:field-conversion', 'dark cyan', 'black'),
    ('cmd:field-format', 'dark cyan', 'black'),

    ('doc:default', 'light gray', 'black'),
    ('doc:parameter', 'dark magenta', 'black'),
    ('doc:type-hint', 'dark cyan', 'black'),
    ('doc:value-hint', 'brown', 'black'),
    ('doc:value-hint:default', 'light cyan', 'black'),
    ('doc:string', 'dark green', 'black'),
    ('doc:number', 'yellow', 'black'),
    ('doc:code-fence', 'dark red', 'black'),
    #
    ('python:default', 'light gray', 'black'),
    ('python:name', 'light gray', 'black'),
    ('python:comment', 'dark gray', 'black'),
    ('python:keyword', 'dark magenta', 'black'),
    ('python:class', 'brown', 'black'),
    ('python:decorator', 'brown', 'black'),
    ('python:string', 'dark green', 'black'),
    ('python:string:escape', 'light cyan', 'black'),
    ('python:string:interp', 'light gray', 'black'),
    ('python:function', 'dark cyan', 'black'),
    ('python:number', 'yellow', 'black'),

    # Diffs
    ('diff:insert', 'dark magenta', 'black', 'standout'),
    ('diff:delete', 'light gray,bold', 'dark red'),
]
