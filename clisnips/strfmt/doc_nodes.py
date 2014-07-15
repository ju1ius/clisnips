from collections import OrderedDict

from ..utils import get_num_decimals
from ..exceptions import ParsingError


class Documentation(object):

    def __init__(self):
        self.header = ''
        self.parameters = OrderedDict()
        self.code_blocks = []

    def __str__(self):
        code = '\n'.join(str(c) for c in self.code_blocks)
        params = '\n'.join(str(p) for p in self.parameters.values())
        return (
            str(self.header)
            + params
            + code
        )

    def __repr__(self):
        return str(self)


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

    def __repr__(self):
        return str(self)


class ValueRange(object):

    def __init__(self, start, end, step=None, default=None):
        self.start = start
        self.end = end
        self.step = self._get_default_step() if step is None else step
        if default is None or default < start:
            default = start
        elif default > end:
            default = end
        self.default = default

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

    def __repr__(self):
        return str(self)


class ValueList(object):

    def __init__(self, values, default=0):
        self.values = values
        self.default = default

    def get_default_value(self):
        return self.values[self.default]

    def __len__(self):
        return len(self.values)

    def __str__(self):
        values = []
        for i, value in enumerate(self.values):
            value = repr(value)
            if i == self.default:
                value = '*' + value
            values.append(value)
        return '[%s]' % ', '.join(values)

    def __repr__(self):
        return str(self)


class CodeBlock(object):

    def __init__(self, code):
        self.code = code
        self._bytecode = compile(code, '<codeblock>', 'exec')

    def execute(self, _vars=None):
        if not _vars:
            _vars = {}
        exec(self._bytecode, _vars)

    def __str__(self):
        return '```\n{code}\n```'.format(code=self.code)

    def __repr__(self):
        return str(self)
