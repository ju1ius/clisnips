from collections import OrderedDict

from ..utils import get_num_decimals
from ..exceptions import ParsingError


class Documentation(object):

    def __init__(self):
        self.header = ''
        self._parameter_list = ParameterList()
        self.code_blocks = []

    @property
    def parameters(self):
        return self._parameter_list

    def __str__(self):
        code = '\n'.join(str(c) for c in self.code_blocks)
        return (
            str(self.header)
            + str(self._parameter_list)
            + code
        )

    def __repr__(self):
        return str(self)


class ParameterList(OrderedDict):

    def __init__(self):
        super(ParameterList, self).__init__()
        self._auto_count = -1
        self._has_numeric_field = False

    def append(self, param):
        if param.name == '':
            if self._has_numeric_field:
                raise ParsingError(
                    'cannot switch from automatic field numbering '
                    'to manual field specification'
                )
            self._auto_count += 1
            param.name = self._auto_count
        else:
            try:
                param.name = int(param.name)
                is_numeric = True
                self._has_numeric_field = True
            except ValueError:
                is_numeric = False
            if is_numeric and self._auto_count > -1:
                raise ParsingError(
                    'cannot switch from automatic field numbering '
                    'to manual field specification'
                )
        self.__setitem__(param.name, param)

    def __setitem__(self, key, value):
        if not isinstance(value, Parameter):
            raise ValueError('ParameterList only accepts Parameter instances')
        super(ParameterList, self).__setitem__(key, value)

    def __str__(self):
        return '\n'.join(str(p) for p in self.values())


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
