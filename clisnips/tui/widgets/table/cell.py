import urwid

from .column import Column


class Cell(urwid.Text):

    def __init__(self, content, column: Column, separator: bool = True, align: str = 'left', separator_attr=None):
        self._content = content
        self.separator = separator
        self._align = align
        self._width = column.computed_width
        self._separator_attr = separator_attr

        content = self._format_content()
        super().__init__(content, align=align, wrap='clip')

    def resize(self, width: int):
        self._width = width
        content = self._format_content()
        self.set_text(content)

    def _format_content(self) -> str:
        content_attr = None
        if not isinstance(self._content, tuple):
            content = str(self._content)
        else:
            content_attr = self._content[0]
            content = str(self._content[1])

        if self.separator:
            content_max_len = self._width - 1
        else:
            content_max_len = self._width

        if len(content) > content_max_len:
            content = content[:content_max_len - 1]
            content += '…'  # '»'
        else:
            if self._align == 'left':
                content = content.ljust(content_max_len)
            else:
                content = content.rjust(content_max_len)

        if content_attr is not None:
            content = (content_attr, content)

        if self.separator:
            if self._separator_attr:
                sep = (self._separator_attr, '|')
            else:
                sep = '|'
            if isinstance(content, list):
                content.append(sep)
            else:
                content = [content, sep]

        return content
