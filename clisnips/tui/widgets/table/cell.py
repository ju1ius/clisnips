import urwid


class Cell(urwid.Text):

    def __init__(self, row, column, content):
        self._row = row
        self._column = column
        super().__init__(content, wrap='space' if column.word_wrap else 'any')
