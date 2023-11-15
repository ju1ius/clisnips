import urwid

from clisnips.stores import SnippetsStore
from clisnips.tui.components.layout_selector import LayoutSelector
from clisnips.tui.components.page_size_input import PageSizeInput
from clisnips.tui.components.sort_colum_selector import SortColumnSelector
from clisnips.tui.components.sort_order_selector import SortOrderSelector
from clisnips.tui.widgets.dialog import Dialog
from clisnips.tui.widgets.divider import HorizontalDivider


class ListOptionsDialog(Dialog):
    def __init__(self, parent, store: SnippetsStore):
        super().__init__(parent, urwid.Pile([
            ('pack', LayoutSelector(store)),
            ('pack', HorizontalDivider()),
            SortColumnSelector(store),
            ('pack', HorizontalDivider()),
            SortOrderSelector(store),
            ('pack', HorizontalDivider()),
            ('pack', PageSizeInput(store, 'Page size: ')),
        ]))
