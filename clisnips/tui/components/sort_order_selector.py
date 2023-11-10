import urwid

from clisnips.database import SortOrder
from clisnips.stores import SnippetsStore

choices = {
    SortOrder.ASC: 'Sort Ascending',
    SortOrder.DESC: 'Sort Descending',
}


class SortOrderSelector(urwid.ListBox):
    def __init__(self, store: SnippetsStore):

        def on_clicked(_, selected: bool, value: SortOrder):
            if selected:
                store.change_sort_order(value)

        group, buttons = [], []
        for order, label in choices.items():
            btn = urwid.RadioButton(group, label)
            urwid.connect_signal(btn, 'change', on_clicked, user_arg=order)
            buttons.append(btn)

        def on_state_changed(value: SortOrder):
            for i, order in enumerate(choices.keys()):
                buttons[i].set_state(value is order, do_callback=False)

        self._watchers = {
            'selected': store.watch(lambda s: s['sort_order'], on_state_changed, immediate=True),
        }

        super().__init__(urwid.SimpleListWalker(buttons))
