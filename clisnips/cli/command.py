import argparse
from typing import Optional

from clisnips.dic import DependencyInjectionContainer
from .utils import UrwidMarkupHelper


class Command:
    @classmethod
    def configure(cls, action: argparse._SubParsersAction):
        return NotImplemented

    def __init__(self, dic: DependencyInjectionContainer):
        self.container = dic
        self._markup_helper = UrwidMarkupHelper()

    def run(self, argv) -> Optional[int]:
        return NotImplemented

    def print(self, *args, stderr: bool = False, end: str = '\n', sep: str = ' '):
        self._markup_helper.print(*args, stderr, end, sep)
