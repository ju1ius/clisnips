import logging

import urwid
from urwid.widget.constants import WrapMode

from clisnips.database import Snippet
from clisnips.stores.snippets import SnippetsStore, State
from clisnips.tui.layouts.table import LayoutColumn, LayoutRow, TableLayout
from clisnips.tui.widgets.list_box import CyclingFocusListBox

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


class SnippetsTable(urwid.WidgetWrap):
    def __init__(self, store: SnippetsStore):
        self._store = store
        self._walker = urwid.SimpleFocusListWalker([])
        super().__init__(CyclingFocusListBox(self._walker))

        layout: TableLayout[Snippet] = TableLayout()
        layout.append_column(LayoutColumn('tag'))
        layout.append_column(LayoutColumn('title', wrap=True))
        layout.append_column(LayoutColumn('cmd', wrap=True))

        def watch_snippets(state: State):
            width, _ = state['viewport']
            return width, [state['snippets_by_id'][k] for k in state['snippet_ids']]

        def on_snippets_changed(args: tuple[int, list[Snippet]]):
            width, snippets = args
            logging.getLogger(__name__).debug(f'width={width}')
            layout.invalidate()
            layout.layout(snippets, width)
            self._walker.clear()
            for index, row in enumerate(layout):
                row = urwid.AttrMap(ListItem(row), ATTR_MAP, FOCUS_ATTR_MAP)
                self._walker.append(row)
            self._invalidate()

        self._watcher = store.watch(watch_snippets, on_snippets_changed, immediate=True, sync=False)

    def get_selected_index(self) -> int | None:
        _, index = self._walker.get_focus()
        return index

    def set_selected_index(self, index: int):
        self._walker.set_focus(index)


class ListItem(urwid.Columns):
    def __init__(self, row: LayoutRow[Snippet]):
        cols = []
        for column, value in row:
            cell = urwid.Text((column.key, value), wrap=WrapMode.SPACE if column.word_wrap else WrapMode.ANY)
            cols.append((column.computed_width, cell))

        super().__init__(cols, dividechars=1)

    def selectable(self) -> bool:
        return True
