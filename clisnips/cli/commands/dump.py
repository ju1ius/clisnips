import argparse
import gzip
import logging
import time
from pathlib import Path
from typing import TextIO

from clisnips.cli.command import Command

logger = logging.getLogger(__name__)


def configure(cmd: argparse.ArgumentParser):
    cmd.add_argument('-c', '--compress', action='store_true', help='Compresses the output using gzip.')
    cmd.add_argument('file', type=Path)

    return DumpCommand


class DumpCommand(Command):
    def run(self, argv) -> int:
        start_time = time.time()
        logger.info(f'Dumping database to {argv.file}')

        if argv.compress:
            with gzip.open(argv.file, 'wt') as fp:
                self._dump(fp)  # type: ignore (the `wt` mode implies TextIO)
        else:
            with open(argv.file, 'w') as fp:
                self._dump(fp)

        elapsed = time.time() - start_time
        logger.info(f'Done in {elapsed:.1f} seconds.', extra={'color': 'success'})
        return 0

    def _dump(self, fp: TextIO):
        db = self.container.database
        for line in db.connection.iterdump():
            fp.write(f'{line}\n')
