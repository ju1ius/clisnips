import time
from typing import Optional

from .command import Command


class OptimizeCommand(Command):

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
