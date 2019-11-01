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
        urwid.connect_signal(self.view, 'page-requested', self._on_page_requested)
        urwid.connect_signal(self.view, 'delete-snippet-requested', self._on_delete_snippet_requested)

        self._model.list()

    def _on_search_term_changed(self, view, text):
        if not text:
            self._model.list()
            return
        self._model.search(text)

    def _on_snippet_selected(self, view, snippet):
        # TODO: show command dialog if needed
        urwid.emit_signal(self, 'snippet-applied', snippet['cmd'])

    def _on_sort_column_selected(self, view, column, order):
        # self._config.pager_sort_column = column
        # self._config.save()
        self._model.set_sort_column(column, order)
        if self._model.is_searching:
            self._model.search(self.view.get_search_text())
        else:
            self._model.list()

    def _on_page_requested(self, view, page):
        if not self._model.must_paginate:
            return
        if page == 'first' and not self._model.is_first_page:
            self._model.first_page()
        elif page == 'last' and not self._model.is_last_page:
            self._model.last_page()
        elif page == 'next' and not self._model.is_last_page:
            self._model.next_page()
        elif page == 'previous' and not self._model.is_first_page:
            self._model.previous_page()

    def _on_delete_snippet_requested(self, view, rowid):
        self._model.delete(rowid)
