import urwid

from clisnips.config import Config
from clisnips.exceptions import ParsingError
from clisnips.syntax import parse_command
from clisnips.tui.models.snippets import SnippetsModel
from clisnips.tui.screen import Screen
from clisnips.tui.views.snippets_list import SnippetListView


class SnippetsListScreen(Screen):

    def __init__(self, config: Config, model: SnippetsModel):
        super().__init__(['snippet-applied'])

        self._config = config
        self._model = model

        self.view = SnippetListView(self._model)
        urwid.connect_signal(self.view, 'search-changed', self. _on_search_term_changed)
        urwid.connect_signal(self.view, 'snippet-selected', self._on_snippet_selected)
        urwid.connect_signal(self.view, 'sort-column-selected', self._on_sort_column_selected)
        urwid.connect_signal(self.view, 'page-size-changed', self._on_page_size_changed)
        urwid.connect_signal(self.view, 'page-requested', self._on_page_requested)
        urwid.connect_signal(self.view, 'apply-snippet-requested', self._on_apply_snippet_requested)
        urwid.connect_signal(self.view, 'delete-snippet-requested', self._on_delete_snippet_requested)
        urwid.connect_signal(self.view, 'edit-snippet-requested', self._on_edit_snippet_requested)
        urwid.connect_signal(self.view, 'create-snippet-requested', self._on_create_snippet_requested)

        self._model.list()

    def _on_search_term_changed(self, view, text):
        if not text:
            self._model.list()
            return
        self._model.search(text)

    def _on_snippet_selected(self, view, snippet):
        try:
            cmd = parse_command(snippet['cmd'])
        except ParsingError as err:
            # TODO: show error
            return
        if not cmd.field_names:
            urwid.emit_signal(self, 'snippet-applied', snippet['cmd'])
            return
        self.view.open_insert_snippet_dialog(snippet)

    def _on_sort_column_selected(self, view, column, order):
        self._model.set_sort_column(column, order)
        self._config.pager_sort_column = column
        self._config.pager_sort_order = order
        if self._model.is_searching:
            self._model.search(self.view.get_search_text())
        else:
            self._model.list()

    def _on_page_size_changed(self, view, page_size):
        self._model.set_page_size(page_size)
        self._config.pager_page_size = page_size

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

    def _on_apply_snippet_requested(self, view, command):
        urwid.emit_signal(self, 'snippet-applied', command)

    def _on_delete_snippet_requested(self, view, rowid):
        self._model.delete(rowid)

    def _on_edit_snippet_requested(self, view, snippet):
        # TODO: validate and proceed or cancel
        self._model.update(snippet)

    def _on_create_snippet_requested(self, view, snippet):
        # TODO: validate and proceed or cancel
        self._model.create(snippet)
