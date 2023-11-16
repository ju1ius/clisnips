import argparse

from clisnips.exporters import export_xml, export_json
from .command import Command


class ExportCommand(Command):
    @classmethod
    def configure(cls, action: argparse._SubParsersAction):
        cmd = action.add_parser('export', help='Exports snippets a file.')
        cmd.add_argument('--format', choices=['xml', 'json'], default='xml')
        cmd.add_argument('file', type=argparse.FileType('w'))

    def run(self, argv) -> int:
        export = export_json if argv.format == 'json' else export_xml
        export(self.container.database, argv.file, self.print)
        return 0
