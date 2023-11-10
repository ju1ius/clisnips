import urwid

from clisnips.database import SortOrder
from clisnips.stores import SnippetsStore
from clisnips.tui.widgets.radio import RadioGroup

choices = {
    SortOrder.ASC: 'Sort Ascending',
    SortOrder.DESC: 'Sort Descending',
}


class SortOrderSelector(urwid.ListBox):
    def __init__(self, store: SnippetsStore):
        group = RadioGroup(choices)
        urwid.connect_signal(group, RadioGroup.Signals.CHANGED, lambda v: store.change_sort_order(v))
        self._watcher = store.watch(
            lambda s: s['sort_order'],
            lambda v: group.set_value(v),
            immediate=True,
        )
        super().__init__(urwid.SimpleListWalker(group))
