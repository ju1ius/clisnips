import urwid


class Store:

    SIGNAL_LOAD = 'store/load'
    SIGNALS = (SIGNAL_LOAD,)

    def __init__(self):
        self._columns = []
        self._rows = []
        urwid.register_signal(self.__class__, self.SIGNALS)

    def load(self, rows):
        self._rows = rows
        urwid.emit_signal(self, self.SIGNAL_LOAD, self)

    @property
    def rows(self):
        return self._rows

    @property
    def columns(self):
        return self._columns

    def get_column(self, key):
        if isinstance(key, int):
            return self._columns[key]
        if isinstance(key, str):
            for column in self._columns:
                if column.name == key:
                    return column

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self._rows[key]
        raise TypeError(f'Table store indices must be int or slice, not {type(key).__name__}')

    def __len__(self):
        return len(self._rows)

    def __iter__(self):
        return iter(self._rows)
