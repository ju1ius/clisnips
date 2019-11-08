import time
from typing import Optional

from .command import Command


class DumpCommand(Command):

    def run(self, argv) -> Optional[int]:
        start_time = time.time()

        db = self.container.database
        for line in db.connection.iterdump():
            argv.file.write(f'{line}\n')

        elapsed = time.time() - start_time
        self.print(('success', f'Success: dumped database to {argv.file.name} in {elapsed:.1f} seconds.'), stderr=True)
        return 0
