import urwid


class SnippetListFooter(urwid.Columns):

    def __init__(self):

        self._pager_infos = urwid.Text('Page 1/1 (0)', wrap='clip')

        widgets = (
            ('pack', urwid.Text('? Help')),
            ('pack', urwid.Text('F1 Sort')),
            ('weight', 2, self._pager_infos),
        )

        super().__init__(widgets, dividechars=1)

    def set_pager_infos(self, current_page: int, page_count: int, row_count: int):
        text = f'Page {current_page}/{page_count} ({row_count})'
        self._pager_infos.set_text(text)
