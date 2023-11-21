import argparse
import logging
import shutil
from pathlib import Path

from pydantic import ValidationError

from clisnips.ty import AnyPath

from .command import Command

logger = logging.getLogger(__name__)


class ImportCommand(Command):
    @classmethod
    def configure(cls, action: argparse._SubParsersAction):
        cmd = action.add_parser('import', help='Imports snippets from a file.')
        cmd.add_argument('-f', '--format', choices=('xml', 'json', 'toml', 'cli-companion'), default=None)
        cmd.add_argument('--replace', action='store_true', help='Replaces snippets. The default is to append.')
        cmd.add_argument('-D', '--dry-run', action='store_true', help='Just pretend.')
        cmd.add_argument('file', type=Path)

    def run(self, argv) -> int:
        cls = self._get_importer_class(argv.format, argv.file.suffix)
        if not cls:
            logger.error(
                f'Could not detect import format for {argv.file}.\n'
                'Please provide an explicit format with the --format option.'
            )
            return 1

        if argv.replace:
            db_path = argv.database or self.container.config.database_path
            self._backup_and_drop_db(db_path, argv.dry_run)
            db = self.container.open_database(db_path)
        else:
            db = self.container.database

        try:
            cls(db, dry_run=argv.dry_run).import_path(argv.file)
        except ValidationError as err:
            logger.error(err)
            return 128

        return 0

    def _get_importer_class(self, format: str | None, suffix: str):
        match format, suffix:
            case ('json', _) | (None, '.json'):
                from clisnips.importers import JsonImporter

                return JsonImporter
            case ('toml', _) | (None, '.toml'):
                from clisnips.importers import TomlImporter

                return TomlImporter
            case ('xml', _) | (None, '.xml'):
                from clisnips.importers import XmlImporter

                return XmlImporter
            case ('cli-companion', _):
                from clisnips.importers import CliCompanionImporter

                return CliCompanionImporter
            case _:
                return None

    def _backup_and_drop_db(self, db_path: AnyPath, dry_run: bool):
        backup_path = self._get_backup_path(db_path)

        logger.warning(f'Backing up database to {backup_path}')
        if not dry_run:
            shutil.copyfile(db_path, backup_path)

        logger.warning('Dropping database!')
        if not dry_run:
            Path(db_path).unlink(True)

    def _get_backup_path(self, path: AnyPath) -> Path:
        backup_path = Path(path).with_suffix('.bak')
        index = 0
        while backup_path.exists() and index < 64:
            backup_path = backup_path.with_suffix(f'.{index}.bak')
            index += 1
        return backup_path
