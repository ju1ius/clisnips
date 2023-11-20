import logging
import time
from pathlib import Path

from .base import Importer, SnippetListAdapter

logger = logging.getLogger(__name__)


class JsonImporter(Importer):
    def import_path(self, path: Path):
        start_time = time.time()
        logger.info(f'Importing snippets from {path}')

        with open(path) as fp:
            data = SnippetListAdapter.validate_json(fp.read())
            if not self._dry_run:
                self._db.insert_many(data)
            logger.info('Rebuilding & optimizing search index')
            if not self._dry_run:
                self._db.rebuild_index()
                self._db.optimize_index()

        elapsed_time = time.time() - start_time
        logger.info(f'Imported in {elapsed_time:.1f} seconds.', extra={'color': 'success'})
