import urwid


class PagerInfos(urwid.Text):

    def __init__(self, model):
        super().__init__('Page 1/1 (0)', align='right')

        model.connect(model.Signals.ROWS_LOADED, self._on_model_updated)
        model.connect(model.Signals.ROW_CREATED, self._on_model_updated)
        model.connect(model.Signals.ROW_DELETED, self._on_model_updated)

    def _on_model_updated(self, model, *args):
        text = f'Page {model.current_page}/{model.page_count} ({model.row_count})'
        self.set_text(text)
