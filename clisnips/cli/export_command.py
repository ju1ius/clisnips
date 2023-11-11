from typing import Optional

from clisnips.exporters import export_xml, export_json
from .command import Command


class ExportCommand(Command):

    def run(self, argv) -> Optional[int]:
        export = export_json if argv.format == 'json' else export_xml
        export(self.container.database, argv.file, self.print)
        return 0
