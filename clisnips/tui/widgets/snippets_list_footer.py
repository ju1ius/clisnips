import urwid


class SnippetListFooter(urwid.Columns):

    def __init__(self, model):
        widgets = (
            ('pack', urwid.Text('F1 Help')),
            ('pack', urwid.Text('F1 Sort')),
            ('pack', urwid.Text('ESC Quit')),
        )
        super().__init__(widgets, dividechars=1)
