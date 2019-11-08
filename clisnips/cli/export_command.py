from typing import Optional

from clisnips.exporters import export_xml
from .command import Command


class ExportCommand(Command):

    def run(self, argv) -> Optional[int]:
        export_xml(self.container.database, argv.file, self.print)
        return 0
