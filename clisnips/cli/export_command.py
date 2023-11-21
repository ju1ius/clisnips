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
        cls = self._get_exporter_class(argv.format, argv.file.suffix)
        if not cls:
            logger.error(
                f'Could not detect export format for {argv.file}.\n'
                'Please provide an explicit format with the --format option.'
            )
            return 1

        cls(self.container.database).export(argv.file)
        return 0

    def _get_exporter_class(self, format: str | None, suffix: str):
        match format, suffix:
            case ('json', _) | (None, '.json'):
                from clisnips.exporters import JsonExporter

                return JsonExporter
            case ('toml', _) | (None, '.toml'):
                from clisnips.exporters import TomlExporter

                return TomlExporter
            case ('xml', _) | (None, '.xml'):
                from clisnips.exporters import XmlExporter

                return XmlExporter
            case _:
                return None
