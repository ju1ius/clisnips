from typing import Optional

from .command import DatabaseCommand
from ..exporters import export_xml


class ExportCommand(DatabaseCommand):

    def run(self, argv) -> Optional[int]:
        db = self.open_database(argv)
        export_xml(db, argv.file, self.print)
        return 0
