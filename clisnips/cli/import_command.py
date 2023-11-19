import argparse
import shutil
from pathlib import Path

from clisnips.database.snippets_db import SnippetsDatabase
from clisnips.ty import AnyPath

from .command import Command


class ImportCommand(Command):
    @classmethod
    def configure(cls, action: argparse._SubParsersAction):
        cmd = action.add_parser('import', help='Imports snippets from a file.')
        cmd.add_argument('-f', '--format', choices=['xml', 'json', 'toml', 'cli-companion'], default='xml')
        cmd.add_argument('--replace', action='store_true', help='Replaces snippets. The default is to append.')
        cmd.add_argument('-D', '--dry-run', action='store_true', help='Just pretend.')
        cmd.add_argument('file', type=Path)

    def run(self, argv) -> int:
        if argv.replace:
            db_path = argv.database or self.container.config.database_path
            self._backup_and_drop_db(db_path, argv.dry_run)
            db = self.container.open_database(db_path)
            self._create_importer(argv.format, db, argv.dry_run).import_path(argv.file)
            return 0

        self._create_importer(argv.format, self.container.database, argv.dry_run).import_path(argv.file)
        return 0

    def _create_importer(self, name: str, db: SnippetsDatabase, dry_run: bool):
        match name:
            case 'json':
                from clisnips.importers import JsonImporter
                return JsonImporter(db, self.print, dry_run=dry_run)
            case 'toml':
                from clisnips.importers import TomlImporter
                return TomlImporter(db, self.print, dry_run=dry_run)
            case 'cli-companion':
                from clisnips.importers import CliCompanionImporter
                return CliCompanionImporter(db, self.print, dry_run=dry_run)
            case 'xml' | _:
                from clisnips.importers import XmlImporter
                return XmlImporter(db, self.print, dry_run=dry_run)


    def _backup_and_drop_db(self, db_path: AnyPath, dry_run: bool):
        backup_path = f'{db_path}.bak'
        self.print(('warning', f'Backing up database to {backup_path}...'))
        if not dry_run:
            shutil.copyfile(db_path, f'{db_path}.bak')
        db = self.container.database
        self.print(('warning', 'Dropping tables...'))
        if not dry_run:
            db.connection.executescript('DROP TABLE snippets_index; DROP TABLE snippets; VACUUM;')
            db.close()
