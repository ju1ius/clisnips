import urwid

from clisnips.stores.snippets import SnippetsStore
from clisnips.tui.components.layout_selector import LayoutSelector
from clisnips.tui.components.page_size_input import PageSizeInput
from clisnips.tui.components.sort_colum_selector import SortColumnSelector
from clisnips.tui.components.sort_order_selector import SortOrderSelector
from clisnips.tui.widgets.dialog import Dialog
from clisnips.tui.widgets.divider import HorizontalDivider


class ListOptionsDialog(Dialog):
    def __init__(self, parent, store: SnippetsStore):
        contents = (
            LayoutSelector(store),
            HorizontalDivider(),
            SortColumnSelector(store),
            SortOrderSelector(store),
            HorizontalDivider(),
            PageSizeInput(store, 'Page size: '),
        )
        super().__init__(parent, urwid.ListBox(urwid.SimpleListWalker(contents)))
