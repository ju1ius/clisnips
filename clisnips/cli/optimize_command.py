import argparse
import logging
import time

from .command import Command

logger = logging.getLogger(__name__)


class OptimizeCommand(Command):
    @classmethod
    def configure(cls, action: argparse._SubParsersAction):
        cmd = action.add_parser('optimize', help='Runs optimization tasks on the database.')
        cmd.add_argument('--rebuild', action='store_true', help='Rebuilds the search index before optimizing.')

    def run(self, argv) -> int:
        start_time = time.time()

        db = self.container.database
        if argv.rebuild:
            logger.info('Rebuilding search index')
            db.rebuild_index()

        logger.info('Optimizing search index')
        db.optimize_index()

        elapsed = time.time() - start_time
        logger.info(f'Done in {elapsed:.1f} seconds.', extra={'color': 'success'})
        return 0
