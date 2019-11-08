from typing import Optional

from .command import Command
from ..exporters import export_xml


class ExportCommand(Command):

    def run(self, argv) -> Optional[int]:
        export_xml(self.container.database, argv.file, self.print)
        return 0
