from copy import deepcopy
from typing import Dict, List

from clisnips.utils.number import get_num_decimals


class Documentation(object):

    def __init__(self):
        self.header: str = ''
        self.parameters: Dict[str, Parameter] = dict()
        self.code_blocks: List[CodeBlock] = []

    def execute_code(self, context: Dict):
        if not self.code_blocks:
            return context
        ctx = deepcopy(context)
        for code in self.code_blocks:
            code.execute(ctx)
        return ctx

    def __str__(self):
        code = '\n'.join(str(c) for c in self.code_blocks)
        params = '\n'.join(str(p) for p in self.parameters.values())
        return f'{self.header!s}{params}{code}'

    def __repr__(self):
        return str(self)


class Parameter(object):

    def __init__(self, name: str, type_hint=None, value_hint=None, text: str = ''):
        self.name = name
        self.type_hint = type_hint
        self.value_hint = value_hint
        self.text = text

    def __str__(self):
        return f'{{{self.name}}} ({self.type_hint}) {self.value_hint} {self.text!r}'

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
        return '[%s..%s:%s*%s]' % (self.start, self.end, self.step, self.default)

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
                value = f'=>{value}'
            values.append(value)
        return '[%s]' % ', '.join(values)

    def __repr__(self):
        return str(self)


class CodeBlock(object):

    def __init__(self, code):
        self.code = code
        self._bytecode = compile(code, '<codeblock>', 'exec')

    def execute(self, context: Dict):
        exec(self._bytecode, context)

    def __str__(self):
        return f'```\n{self.code}\n```'

    def __repr__(self):
        return str(self)
