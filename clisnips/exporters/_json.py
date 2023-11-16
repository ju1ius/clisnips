import json
from pathlib import Path
import time

from clisnips.exporters.base import Exporter


class JsonExporter(Exporter):
    def export(self, path: Path):
        start_time = time.time()
        num_rows = len(self._db)
        self._log(('info', f'Converting {num_rows:n} snippets to JSON...'))

        with open(path, 'w') as fp:
            json.dump([dict(row) for row in self._db], fp, indent=2)

        elapsed_time = time.time() - start_time
        self._log(('success', f'Success: exported {num_rows:n} snippets in {elapsed_time:.1f} seconds.'))
