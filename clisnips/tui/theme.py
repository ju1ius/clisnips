

palette = [
    # (name, foreground, background, mono=None, foreground_high=None, background_high=None)
    ('default', 'light gray', 'black'),
    ('view:default', 'light gray', 'black'),
    ('search-entry:caption', 'dark cyan', 'black'),

    ('table-row:focused', 'black', 'light gray', 'standout'),
    ('table-column:cmd', 'light gray', 'black'),
    ('table-column:cmd:focused', 'black', 'light gray', 'standout'),
    ('table-column:title', 'light gray,italics', 'black'),
    ('table-column:title:focused', 'black,italics', 'light gray', 'standout'),
    ('table-column:tag', 'brown', 'black'),
    ('table-column:tag:focused', 'black', 'light gray', 'standout'),

    # Syntax highlighting
    ('doc:header', 'light gray', 'black'),
    ('doc:param:name', 'dark magenta', 'black'),
    ('doc:param:type-hint', 'dark cyan', 'black'),
    ('doc:param:value-hint', 'brown', 'black'),
    ('doc:param:text', 'light gray', 'black'),
    ('doc:code', 'dark green', 'black'),

    ('cmd:default', 'light gray', 'black'),
    ('cmd:param', 'dark magenta', 'black'),
    ('cmd:conv', 'dark cyan', 'black'),
    ('cmd:spec', 'brown', 'black'),

    # Diffs
    ('diff:ins', 'black,bold', 'dark green', 'standout'),
    ('diff:del', 'white,bold', 'dark red'),

    # Buttons
    ('button:suggested', 'dark cyan,bold', 'black'),
    ('button:destructive', 'dark red,bold', 'black'),

    ('error', 'white', 'dark red'),
    ('warning', 'black', 'brown'),
    ('info', 'white', 'dark blue', '', 'h186', 'g20'),
]
