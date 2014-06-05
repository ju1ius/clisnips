from ..utils import get_num_decimals


class Documentation(object):

    def __init__(self, text, params):
        self.text = text
        self.parameters = params


class Parameter(object):

    def __init__(self, name, typehint=None, valuehint=None, text=None):
        self.name = name
        self.typehint = typehint
        self.valuehint = valuehint
        self.text = text

    def __str__(self):
        return '{%s} (%s) %s "%s"' % (
            self.name, self.typehint,
            self.valuehint, self.text
        )


class ValueRange(object):

    def __init__(self, start, end, step=None, default=None):
        self.start = start
        self.end = end
        self.step = self._get_default_step() if step is None else step
        self.default = default if default is not None else start

    def _get_default_step(self):
        start_decimals = get_num_decimals(self.start)
        end_decimals = get_num_decimals(self.end)
        if start_decimals == 0 and end_decimals == 0:
            return 1
        n = max(start_decimals, end_decimals)
        return float('0.' + '0' * (n - 1) + '1')

    def __str__(self):
        return '[%s..%s:%s*%s]' % (
            self.start, self.end, self.step, self.default
        )


class ValueList(object):

    def __init__(self, values, default=0):
        self.values = values
        self.default = default

    def get_default_value(self):
        return self.values[self.default]
