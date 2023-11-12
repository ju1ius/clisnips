from typing import Optional

import urwid

from clisnips.database.snippets_db import Snippet
from clisnips.stores.snippets import SnippetsStore
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

class SnippetsList(CyclingFocusListBox):

    def __init__(self, store: SnippetsStore):
        walker = urwid.SimpleFocusListWalker([])
        super().__init__(walker)

        def watch_snippets(state):
            return [state['snippets_by_id'][k] for k in state['snippet_ids']]

        def on_snippets_changed(snippets: list[Snippet]):
            walker.clear()
            for snippet in snippets:
                walker.append(urwid.AttrMap(
                    ListItem(snippet),
                    attr_map=ATTR_MAP,
                    focus_map=FOCUS_ATTR_MAP,
                ))

        self._watcher = store.watch(watch_snippets, on_snippets_changed, immediate=True)
        self._store = store
        
    def get_selected_index(self) -> Optional[int]:
        _, index = self._body.get_focus()
        return index

    def get_selected(self) -> Optional[Snippet]:
        widget, index = self._body.get_focus()
        if index is not None:
            rowid = self._store.state['snippet_ids'][index]
            return self._store.state['snippets_by_id'][rowid]


class ListItem(urwid.Pile):
    def __init__(self, snippet: Snippet):
        header = urwid.Columns(
            [
                ('weight', 1, urwid.Text(('title', snippet['title']))),
                ('pack', urwid.Text(('tag', f'[{snippet["tag"]}]'))),
            ],
            dividechars=1,
        )
        super().__init__([
            ('pack', header),
            ('pack', urwid.Text(('cmd', snippet['cmd']))),
        ])
        
    def selectable(self) -> bool:
        return True
