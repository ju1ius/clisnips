class UrwidMarkupWriter:
    def __init__(self):
        self._markup = []

    def write(self, text_attr):
        self._markup.append(text_attr)

    def clear(self):
        self._markup = []

    def get_markup(self):
        return self._markup
