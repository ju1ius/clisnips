import argparse
from pathlib import Path

from .command import Command


class ExportCommand(Command):
    @classmethod
    def configure(cls, action: argparse._SubParsersAction):
        cmd = action.add_parser('export', help='Exports snippets to a file.')
        cmd.add_argument('-f', '--format', choices=['xml', 'json'], default='xml')
        cmd.add_argument('file', type=Path)

    def run(self, argv) -> int:
        self._create_exporter(argv.format).export(argv.file)
        return 0

    def _create_exporter(self, name: str):
        match name:
            case 'json':
                from clisnips.exporters import JsonExporter
                return JsonExporter(self.container.database, self.print)
            case 'xml' | _:
                from clisnips.exporters import XmlExporter
                return XmlExporter(self.container.database, self.print)
