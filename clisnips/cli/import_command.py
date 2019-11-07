import shutil
from typing import Optional

from .command import DatabaseCommand
from ..importers import import_cli_companion, import_xml


class ImportCommand(DatabaseCommand):

    def run(self, argv) -> Optional[int]:
        importer = import_cli_companion if argv.format == 'cli-companion' else import_xml
        if argv.replace:
            db_path = argv.database or self.config.database_path
            backup_path = f'{db_path}.bak'
            self.print(('warning', f'Backing up database to {backup_path}...'))
            shutil.copyfile(db_path, f'{db_path}.bak')
            db = self.open_database(argv)
            self.print(('warning', f'Dropping tables...'))
            db.connection.executescript('DROP TABLE snippets_index; DROP TABLE snippets; VACUUM;')
            db.close()
            db = self.open_database(argv)
            importer(db, argv.file, self.print)
            return 0
        db = self.open_database(argv)
        importer(db, argv.file, self.print)
        return 0
