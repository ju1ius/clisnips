import enum
import logging

import urwid

from clisnips.stores.snippets import SnippetsStore
from clisnips.tui.screen import Screen
from clisnips.tui.views.snippets_list import SnippetListView

logger = logging.getLogger(__name__)


class SnippetsListScreen(Screen):

    class Signals(enum.Enum):
        SNIPPET_APPLIED = 'snippet-applied'
        HELP_REQUESTED = 'help-requested'

    def __init__(self, store: SnippetsStore):
        super().__init__(list(self.Signals))
        self.view = SnippetListView(store)
        signals = SnippetListView.Signals
        urwid.connect_signal(self.view, signals.APPLY_SNIPPET_REQUESTED, self._on_apply_snippet_requested)

    def _on_apply_snippet_requested(self, _, command):
        urwid.emit_signal(self, self.Signals.SNIPPET_APPLIED, command)
