import urwid


class SnippetListFooter(urwid.Columns):

    def __init__(self, model):
        self._pager_infos = urwid.Text('Page 1/1 (0)', wrap='clip')
        widgets = (
            ('pack', urwid.Text('? Help')),
            ('pack', urwid.Text('F1 Sort')),
            ('weight', 2, self._pager_infos),
        )
        super().__init__(widgets, dividechars=1)

        model.connect(model.Signals.ROWS_LOADED, self._on_model_updated)
        model.connect(model.Signals.ROW_CREATED, self._on_model_updated)
        model.connect(model.Signals.ROW_DELETED, self._on_model_updated)

    def _on_model_updated(self, model, *args):
        text = f'Page {model.current_page}/{model.page_count} ({model.row_count})'
        self._pager_infos.set_text(text)
