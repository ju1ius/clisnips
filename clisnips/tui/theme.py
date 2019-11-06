

palette = [
    # (name, foreground, background, mono=None, foreground_high=None, background_high=None)
    ('default', 'light gray', 'black'),
    ('view:default', 'light gray', 'black'),
    ('search-entry:caption', 'dark cyan', 'black'),

    # Buttons
    ('button:suggested', 'dark cyan,bold', 'black'),
    ('button:destructive', 'dark red,bold', 'black'),

    ('error', 'white', 'dark red'),
    ('warning', 'black', 'brown'),
    ('info', 'white', 'dark blue', '', 'h186', 'g20'),

    ('table-row:focused', 'light gray', 'dark gray', 'standout'),
    ('table-column:cmd', 'dark green', 'black'),
    ('table-column:cmd:focused', 'dark green', 'dark gray', 'standout'),
    ('table-column:title', 'light gray,italics', 'black'),
    ('table-column:title:focused', 'light gray,italics', 'dark gray', 'standout'),
    ('table-column:tag', 'brown', 'black'),
    ('table-column:tag:focused', 'brown', 'dark gray', 'standout'),

    # Syntax highlighting
    ('cmd:default', 'dark green', 'black'),
    ('cmd:param', 'dark magenta', 'black'),
    ('cmd:conv', 'dark cyan', 'black'),
    ('cmd:spec', 'brown', 'black'),

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
    ('diff:ins', 'black,bold', 'dark green', 'standout'),
    ('diff:del', 'white,bold', 'dark red'),
]
