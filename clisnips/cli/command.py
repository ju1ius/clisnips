import os
import sys
from typing import Optional

from clisnips.dic import DependencyInjectionContainer
from .utils import UrwidMarkupHelper


class Command:

    def __init__(self, dic: DependencyInjectionContainer):
        self.container = dic
        self._markup_helper = UrwidMarkupHelper()

    def run(self, argv) -> Optional[int]:
        return NotImplemented

    def print(self, *args, stderr=False, end='\n'):
        stream = sys.stderr if stderr else sys.stdout
        tty = os.isatty(stream.fileno())
        output = ' '.join(self._markup_helper.convert_markup(m, tty) for m in args)
        print(output, end=end, file=stream)
