import urwid

from clisnips.tui.logging import logger
from clisnips.tui.models.snippets import SnippetsModel
from clisnips.tui.widgets.dialog import Dialog
from clisnips.tui.widgets.divider import HorizontalDivider


class ListOptionsDialog(Dialog):

    signals = ['sort-changed', 'page-size-changed']

    column_choices = {
        'ranking': 'Sort by popularity',
        'usage_count': 'Sort by usage count',
        'last_used_at': 'Sort by last usage date',
        'created_at': 'Sort by creation date',
    }
    order_choices = {
        'ASC': 'Sort Ascending',
        'DESC': 'Sort Descending',
    }

    def __init__(self, parent, model: SnippetsModel):

        self._model = model
        sort_column, sort_order = model.sort_column
        logger.debug('%s, %s', sort_column, sort_order)

        column_group, column_choices = [], []
        for value, label in self.column_choices.items():
            selected = sort_column == value
            btn = urwid.RadioButton(column_group, label, state=selected,
                                    on_state_change=self._on_column_choice_changed, user_data=value)
            column_choices.append(btn)
        column_list = urwid.ListBox(urwid.SimpleListWalker(column_choices))

        order_group, order_choices = [], []
        for value, label in self.order_choices.items():
            selected = sort_order == value
            btn = urwid.RadioButton(order_group, label, state=selected,
                                    on_state_change=self._on_order_choice_changed, user_data=value)
            order_choices.append(btn)
        order_list = urwid.ListBox(urwid.SimpleListWalker(order_choices))

        page_size = urwid.IntEdit('Page size: ', model.page_size)
        urwid.connect_signal(page_size, 'postchange', self._on_page_size_changed)

        body = urwid.Pile([
            column_list,
            ('pack', HorizontalDivider()),
            order_list,
            ('pack', HorizontalDivider()),
            ('pack', page_size),
        ])

        super().__init__(parent, body)

    def _on_column_choice_changed(self, button, selected, value):
        if selected:
            sort_column, sort_order = self._model.sort_column
            self._emit('sort-changed', value, sort_order)

    def _on_order_choice_changed(self, button, selected, value):
        if selected:
            sort_column, sort_order = self._model.sort_column
            self._emit('sort-changed', sort_column, value)

    def _on_page_size_changed(self, edit, value):
        self._emit('page-size-changed', value)
