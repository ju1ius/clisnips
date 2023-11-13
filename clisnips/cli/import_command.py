import argparse
import shutil
from typing import Optional

from clisnips.importers import import_cli_companion, import_xml
from .command import Command


class ImportCommand(Command):
    @classmethod
    def configure(cls, action: argparse._SubParsersAction):
        cmd = action.add_parser('import', help='Imports snippets from a file.')
        cmd.add_argument('--format', choices=['xml', 'cli-companion'], default='xml')
        cmd.add_argument('--replace', action='store_true', help='Replaces snippets. The default is to append.')
        cmd.add_argument('file', type=argparse.FileType('r'))

    def run(self, argv) -> Optional[int]:
        importer = import_cli_companion if argv.format == 'cli-companion' else import_xml

        if argv.replace:
            db_path = argv.database or self.container.config.database_path
            backup_path = f'{db_path}.bak'
            self.print(('warning', f'Backing up database to {backup_path}...'))
            shutil.copyfile(db_path, f'{db_path}.bak')
            db = self.container.database
            self.print(('warning', 'Dropping tables...'))
            db.connection.executescript('DROP TABLE snippets_index; DROP TABLE snippets; VACUUM;')
            db.close()
            db = self.container.open_database(db_path)
            importer(db, argv.file, self.print)
            return 0

        importer(self.container.database, argv.file, self.print)
        return 0
