from copy import deepcopy
from types import CodeType
from typing import Any

from .nodes import Documentation


class Executor:
    def __init__(self, doc: Documentation) -> None:
        self._doc = doc
        self._bytecode_cache: list[CodeType] = []

    @staticmethod
    def compile_str(code: str) -> CodeType:
        return compile(code, '<codeblock>', 'exec')

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        if not self._doc.code_blocks:
            return context
        if not self._bytecode_cache:
            self._compile_cache()
        ctx = deepcopy(context)
        for code in self._bytecode_cache:
            exec(code, ctx)
        return ctx

    def _compile_cache(self):
        self._bytecode_cache = [self.compile_str(b.code) for b in self._doc.code_blocks]
