import urwid

from clisnips.stores.snippets import ListLayout, SnippetsStore
from clisnips.tui.widgets.switch import Switch


class LayoutSelector(urwid.WidgetWrap):
    def __init__(self, store: SnippetsStore):
        # TODO: change selected state color
        switch = Switch(caption='Layout: ', off_label='List', on_label='Table')
        super().__init__(switch)

        def handle_switch_changed(_, state: Switch.State):
            match state:
                case Switch.State.OFF:
                    store.change_layout(ListLayout.LIST)
                case Switch.State.ON:
                    store.change_layout(ListLayout.TABLE)
        urwid.connect_signal(switch, Switch.Signals.CHANGED, handle_switch_changed)

        def handle_store_changed(layout: ListLayout):
            match layout:
                case ListLayout.LIST:
                    switch.set_state(Switch.State.OFF)
                case ListLayout.TABLE:
                    switch.set_state(Switch.State.ON)
        self._watcher = store.watch(lambda s: s['list_layout'], handle_store_changed, immediate=True)
