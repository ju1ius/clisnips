
from .edit import EmacsEdit


class SearchEntry(EmacsEdit):

    def __init__(self):
        super().__init__('Search term: ', multiline=False)

    def get_search_text(self):
        # urwid.Edit.get_text() returns the caption by default...
        return self.get_edit_text()
