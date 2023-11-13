import argparse
import os
import sys
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
        stream = sys.stderr if stderr else sys.stdout
        tty = os.isatty(stream.fileno())
        output = sep.join(self._markup_helper.convert_markup(m, tty) for m in args)
        print(output, end=end, file=stream)
