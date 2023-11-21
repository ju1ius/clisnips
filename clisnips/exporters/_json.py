import json
import logging
import time
from pathlib import Path

from clisnips.exporters.base import Exporter

logger = logging.getLogger(__name__)


class JsonExporter(Exporter):
    def export(self, path: Path):
        start_time = time.time()
        num_rows = len(self._db)
        logger.info(f'Converting {num_rows:n} snippets to JSON')

        with open(path, 'w') as fp:
            json.dump([dict(row) for row in self._db], fp, indent=2)

        elapsed_time = time.time() - start_time
        logger.info(f'Exported {num_rows:n} snippets in {elapsed_time:.1f} seconds.', extra={'color': 'success'})
