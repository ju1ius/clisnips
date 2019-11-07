import sys
from typing import Optional

from .command import ConfigCommand


class ShowConfigCommand(ConfigCommand):

    def run(self, argv) -> Optional[int]:
        self.config.write(sys.stdout)
        return 0
