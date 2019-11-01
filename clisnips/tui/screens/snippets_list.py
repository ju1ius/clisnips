import urwid

from ..models.snippets import SnippetsModel
from ..screen import Screen
from ..views.snippets_list import SnippetListView


class SnippetsListScreen(Screen):

    def __init__(self, model: SnippetsModel):
        super().__init__(['snippet-applied'])

        self._model = model

        self.view = SnippetListView(self._model)
        urwid.connect_signal(self.view, 'search-changed', self. _on_search_term_changed)
        urwid.connect_signal(self.view, 'snippet-selected', self._on_snippet_selected)
        urwid.connect_signal(self.view, 'sort-column-selected', self._on_sort_column_selected)

        self._model.list()

    def _on_search_term_changed(self, view, text):
        if not text:
            self._model.list()
            return
        self._model.search(text)

    def _on_snippet_selected(self, view, row):
        # TODO: show command dialog if needed
        urwid.emit_signal(self, 'snippet-applied', row['cmd'])

    def _on_sort_column_selected(self, view, column, order):
        # self._config.pager_sort_column = column
        # self._config.save()
        self._model.set_sort_column(column, order)
        if self._model.is_searching:
            self._model.search(self.view.get_search_text())
        else:
            self._model.list()
