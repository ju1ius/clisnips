

palette = [
    # (name, foreground, background, mono=None, foreground_high=None, background_high=None)
    ('diff:ins', 'black,bold', 'dark green', 'standout'),
    ('diff:del', 'white,bold', 'dark red'),

    ('error_message', 'white', 'dark red'),
    ('warning_message', 'black', 'brown'),
    ('info_message', 'white', 'dark blue', '', 'h186', 'g20'),

    ('action_bar', 'black', 'light gray', '', 'h250', 'g20'),
    ('action_bar:action', 'white', 'dark blue', '', 'g80', 'g30'),
    ('action_bar:action_key', 'light red,bold', 'dark blue', '', 'h122,bold', 'g30'),
    # ('action_bar:content', 'light gray', '', '', 'light gray', ''),
    ('action_bar:content', '', '', '', '', ''),

    ('linebox', '', '', '', 'h186', ''),

    ('session_header', 'light red', '', '', 'h186,bold', 'g20'),

    ('command_bar', 'white', 'dark blue', '', 'h117', 'g20'),

    ('list:item:unfocused', '', '', 'standout'),
    ('list:item:focused', 'black', 'light gray', 'standout'),

    ('editbox', 'white', 'dark blue', '', 'g20,bold', 'h144'),
    ('editbox:label', '', ''),

    ('theader', 'light cyan', ''),
    ('theader_sep', 'dark cyan', ''),

    ('trow_focused', 'black', 'light gray'),
    ('tcell_more', 'light red', ''),

    ('tfooter', 'light red', '', '', 'h186', 'g10'),

    # sql syntax highlighting
    ('sql:default', '', ''),
    ('sql:keyword', 'dark cyan', '', '', 'h210,bold', ''),
    ('sql:function', 'dark cyan', '', '', 'h117', ''),
    ('sql:name', 'light gray', '', '', 'h186', ''),
    ('sql:punctuation', 'yellow', '', '', 'h122', ''),
    ('sql:number', 'dark green', '', '', 'h211', ''),
    ('sql:operator', '', ''),
    ('sql:string', 'light cyan', '', '', 'h202', ''),
    ('sql:keyword.type', 'dark cyan', '', '', 'h210', ''),
    ('sql:builtin', 'dark cyan', '', '', 'h186', ''),
]
