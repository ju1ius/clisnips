import time
from typing import Optional

from .command import DatabaseCommand


class DumpCommand(DatabaseCommand):

    def run(self, argv) -> Optional[int]:
        start_time = time.time()

        db = self.open_database(argv)
        for line in db.connection.iterdump():
            argv.file.write(f'{line}\n')

        elapsed = time.time() - start_time
        self.print(('success', f'Success: dumped database to {argv.file.name} in {elapsed:.1f} seconds.'), stderr=True)
        return 0
