import urwid


class SearchEntry(urwid.Edit):

    def __init__(self):
        super().__init__('Search term: ', multiline=False)

    def get_search_text(self):
        # urwid.Edit.get_text() returns the caption by default...
        return self.get_edit_text()

    def keypress(self, size, key):
        return super().keypress(size, key)
