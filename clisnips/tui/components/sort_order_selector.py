import urwid

from clisnips.database import SortOrder
from clisnips.stores.snippets import SnippetsStore
from clisnips.tui.widgets.switch import Switch


class SortOrderSelector(urwid.WidgetWrap):
    def __init__(self, store: SnippetsStore):
        switch = Switch(
            caption='Order: ',
            labels={Switch.State.OFF: '↑ ASC', Switch.State.ON: 'DESC ↓'},
            states={Switch.State.OFF: SortOrder.ASC, Switch.State.ON: SortOrder.DESC},
        )
        super().__init__(switch)

        urwid.connect_signal(switch, Switch.Signals.CHANGED, lambda _, v: store.change_sort_order(v))
        self._watcher = store.watch(
            lambda s: s['sort_order'],
            lambda v: switch.set_value(v),
            immediate=True,
        )
