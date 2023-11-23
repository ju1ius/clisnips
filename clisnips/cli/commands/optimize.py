import argparse
import logging
import time

from clisnips.cli.command import Command

logger = logging.getLogger(__name__)


def configure(cmd: argparse.ArgumentParser):
    cmd.add_argument('--rebuild', action='store_true', help='Rebuilds the search index before optimizing.')

    return OptimizeCommand


class OptimizeCommand(Command):
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
