import urwid


class SearchEntry(urwid.Edit):

    def __init__(self):
        super().__init__('Search term: ', multiline=False)

    def keypress(self, size, key):
        return super().keypress(size, key)
