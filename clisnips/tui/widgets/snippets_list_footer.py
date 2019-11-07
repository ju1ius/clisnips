import urwid


class SnippetListFooter(urwid.Columns):

    def __init__(self, model):
        widgets = (
            ('pack', urwid.Text('? Help')),
            ('pack', urwid.Text('F1 Sort')),
        )
        super().__init__(widgets, dividechars=1)
