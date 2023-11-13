import argparse
import sys
import time
from typing import Optional

from .command import Command


class DumpCommand(Command):
    @classmethod
    def configure(cls, action: argparse._SubParsersAction):
        cmd = action.add_parser('dump', help='Runs a SQL dump of the database.')
        cmd.add_argument('file', type=argparse.FileType('w'), default=sys.stdout)

    def run(self, argv) -> Optional[int]:
        start_time = time.time()

        db = self.container.database
        for line in db.connection.iterdump():
            argv.file.write(f'{line}\n')

        elapsed = time.time() - start_time
        self.print(('success', f'Success: dumped database to {argv.file.name} in {elapsed:.1f} seconds.'), stderr=True)
        return 0
