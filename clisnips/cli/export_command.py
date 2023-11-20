import argparse
import logging
from pathlib import Path

from .command import Command

logger = logging.getLogger(__name__)


class ExportCommand(Command):
    @classmethod
    def configure(cls, action: argparse._SubParsersAction):
        cmd = action.add_parser('export', help='Exports snippets to a file.')
        cmd.add_argument('-f', '--format', choices=('xml', 'json', 'toml'), default=None)
        cmd.add_argument('file', type=Path)

    def run(self, argv) -> int:
        if not argv.format:
            match argv.file.suffix:
                case '.json':
                    argv.format = 'json'
                case '.toml':
                    argv.format = 'toml'
                case '.xml':
                    argv.format = 'xml'
                case _:
                    logger.error(
                        f'Could not detect export format for {argv.file}.\n'
                        'Please provide an explicit format with the --format option.'
                    )
                    return 1

        self._create_exporter(argv.format).export(argv.file)
        return 0

    def _create_exporter(self, name: str):
        match name:
            case 'json':
                from clisnips.exporters import JsonExporter
                return JsonExporter(self.container.database)
            case 'toml':
                from clisnips.exporters import TomlExporter
                return TomlExporter(self.container.database)
            case 'xml' | _:
                from clisnips.exporters import XmlExporter
                return XmlExporter(self.container.database)
