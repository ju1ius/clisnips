import urwid

from clisnips.database import SortColumn
from clisnips.stores.snippets import SnippetsStore
from clisnips.tui.widgets.radio import RadioGroup

choices = {
    SortColumn.RANKING: 'Sort by popularity',
    SortColumn.USAGE_COUNT: 'Sort by usage count',
    SortColumn.LAST_USED_AT: 'Sort by last usage date',
    SortColumn.CREATED_AT: 'Sort by creation date',
}


class SortColumnSelector(urwid.Pile):
    def __init__(self, store: SnippetsStore):
        group = RadioGroup(choices)
        urwid.connect_signal(group, RadioGroup.Signals.CHANGED, lambda v: store.change_sort_column(v))
        self._watcher = store.watch(
            lambda s: s['sort_by'],
            lambda v: group.set_value(v),
            immediate=True,
        )
        super().__init__(group)
