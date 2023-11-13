import argparse
import time
from typing import Optional

from .command import Command


class OptimizeCommand(Command):
    @classmethod
    def configure(cls, action: argparse._SubParsersAction):
        cmd = action.add_parser('optimize', help='Runs optimization tasks on the database.')
        cmd.add_argument('--rebuild', action='store_true', help='Rebuilds the search index before optimizing.')

    def run(self, argv) -> Optional[int]:
        start_time = time.time()

        db = self.container.database
        if argv.rebuild:
            self.print(('info', 'Rebuilding search index...'))
            db.rebuild_index()
        self.print(('info', 'Optimizing search index...'))
        db.optimize_index()

        elapsed = time.time() - start_time
        self.print(('success', f'Success: done in {elapsed:.1f} seconds.'))
        return 0
