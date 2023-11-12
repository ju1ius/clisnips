import logging
from typing import Optional

import observ
import urwid
from urwid.widget.constants import WrapMode

from clisnips.database.snippets_db import Snippet
from clisnips.stores.snippets import SnippetsStore
from clisnips.tui.layouts.table import TableLayout
from clisnips.tui.widgets.list_box import CyclingFocusListBox
from clisnips.tui.layouts.table import LayoutColumn
from clisnips.tui.layouts.table import LayoutRow

ATTR_MAP = {
    None: 'snippets-list',
    'title': 'snippets-list:title',
    'tag': 'snippets-list:tag',
    'cmd': 'snippets-list:cmd',
}

FOCUS_ATTR_MAP = {
    None: 'snippets-list:focused',
    'title': 'snippets-list:title:focused',
    'tag': 'snippets-list:tag:focused',
    'cmd': 'snippets-list:cmd:focused',
}

class SnippetsTable(CyclingFocusListBox):

    def __init__(self, store: SnippetsStore):
        walker = urwid.SimpleFocusListWalker([])
        super().__init__(walker)
        
        self._widget_size = observ.reactive((0, 0))
        self._layout: TableLayout[Snippet] = TableLayout()
        self._layout.append_column(LayoutColumn('tag'))
        self._layout.append_column(LayoutColumn('title', wrap=True))
        self._layout.append_column(LayoutColumn('cmd', wrap=True))

        def watch_snippets(state):
            width = self._widget_size[0]
            return width, [state['snippets_by_id'][k] for k in state['snippet_ids']]

        def on_snippets_changed(args):
            width, snippets = args
            logging.getLogger(__name__).debug(f'render width: {width}')
            self._layout.layout(snippets, width)
            walker.clear()
            for index, row in enumerate(self._layout):
                row = urwid.AttrMap(ListItem(row), ATTR_MAP, FOCUS_ATTR_MAP)
                walker.append(row)
            self._invalidate()

        self._watcher = store.watch(watch_snippets, on_snippets_changed, immediate=True, sync=False)
        # self._size_w = observ.watch(self._widget_size, on_snippets_changed, immediate=True)
        self._store = store
        
    def get_selected_index(self) -> Optional[int]:
        _, index = self._body.get_focus()
        return index

    def render(self, size: tuple[int, int], focus: bool = False):
        logging.getLogger(__name__).debug(f'render size: {size!r}')
        self._widget_size = size
        r = super().render(size, focus)
        return r


class ListItem(urwid.Columns):
    def __init__(self, row: LayoutRow[Snippet]):
        cols = []
        for column, value in row:
            cell = urwid.Text((column.key, value), wrap=WrapMode.SPACE if column.word_wrap else WrapMode.ANY)
            cols.append((column.computed_width, cell))

        super().__init__(cols, dividechars=1)
        
    def selectable(self) -> bool:
        return True
