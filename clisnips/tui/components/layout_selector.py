import urwid

from clisnips.stores.snippets import ListLayout, SnippetsStore
from clisnips.tui.widgets.switch import Switch


class LayoutSelector(urwid.WidgetWrap):
    def __init__(self, store: SnippetsStore):
        switch = Switch(
            caption='Layout: ',
            labels={Switch.State.OFF: 'list', Switch.State.ON: 'table'},
            states={Switch.State.OFF: ListLayout.LIST, Switch.State.ON: ListLayout.TABLE},
        )
        super().__init__(switch)

        urwid.connect_signal(switch, Switch.Signals.CHANGED, lambda _, v: store.change_layout(v))
        self._watcher = store.watch(
            lambda s: s['list_layout'],
            lambda v: switch.set_value(v),
            immediate=True,
        )
