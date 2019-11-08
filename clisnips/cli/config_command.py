import sys
from typing import Optional

from .command import Command


class ShowConfigCommand(Command):

    def run(self, argv) -> Optional[int]:
        self.container.config.write(sys.stdout)
        return 0
