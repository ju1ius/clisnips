import json
from pathlib import Path
import time

from .base import Importer


class JsonImporter(Importer):
    def import_path(self, path: Path):
        start_time = time.time()
        self._log(('info', f'Importing snippets from {path}...'))

        with open(path) as fp:
            data = json.load(fp)
            if not self._dry_run:
                self._db.insert_many(data)
            self._log(('info', 'Rebuilding & optimizing search index...'))
            if not self._dry_run:
                self._db.rebuild_index()
                self._db.optimize_index()

        elapsed_time = time.time() - start_time
        self._log(('success', f'Success: imported in {elapsed_time:.1f} seconds.'))
