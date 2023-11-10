import urwid

from clisnips.database import SortColumn
from clisnips.stores import SnippetsStore

choices = {
    SortColumn.RANKING: 'Sort by popularity',
    SortColumn.USAGE_COUNT: 'Sort by usage count',
    SortColumn.LAST_USED_AT: 'Sort by last usage date',
    SortColumn.CREATED_AT: 'Sort by creation date',
}


class SortColumnSelector(urwid.ListBox):
    def __init__(self, store: SnippetsStore):

        def on_clicked(_, selected: bool, value: SortColumn):
            if selected:
                store.change_sort_column(value)

        group, buttons = [], []
        for column, label in choices.items():
            btn = urwid.RadioButton(group, label)
            urwid.connect_signal(btn, 'change', on_clicked, user_arg=column)
            buttons.append(btn)

        def on_state_changed(value: SortColumn):
            for i, column in enumerate(choices.keys()):
                buttons[i].set_state(value is column, do_callback=False)

        self._watchers = {
            'selected': store.watch(lambda s: s['sort_by'], on_state_changed, immediate=True),
        }

        super().__init__(urwid.SimpleListWalker(buttons))
