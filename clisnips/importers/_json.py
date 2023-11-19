from pathlib import Path
import time

from pydantic import TypeAdapter

from .base import ImportableSnippet, Importer

_SnippetList = TypeAdapter(list[ImportableSnippet])


class JsonImporter(Importer):
    def import_path(self, path: Path):
        start_time = time.time()
        self._log(('info', f'Importing snippets from {path}...'))

        with open(path) as fp:
            # data = json.load(fp)
            data = _SnippetList.validate_json(fp.read())
            if not self._dry_run:
                self._db.insert_many(data) # type: ignore
            self._log(('info', 'Rebuilding & optimizing search index...'))
            if not self._dry_run:
                self._db.rebuild_index()
                self._db.optimize_index()

        elapsed_time = time.time() - start_time
        self._log(('success', f'Success: imported in {elapsed_time:.1f} seconds.'))
