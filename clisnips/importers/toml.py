import logging
import time
from pathlib import Path

import tomllib

from .base import Importer, SnippetDocumentAdapter

logger = logging.getLogger(__name__)


class TomlImporter(Importer):
    def import_path(self, path: Path) -> None:
        start_time = time.time()
        logger.info(f'Importing snippets from {path}')

        with open(path, 'rb') as fp:
            data = SnippetDocumentAdapter.validate_python(tomllib.load(fp))
            if not self._dry_run:
                self._db.insert_many(data['snippets'])
            logger.info('Rebuilding & optimizing search index')
            if not self._dry_run:
                self._db.rebuild_index()
                self._db.optimize_index()

        elapsed_time = time.time() - start_time
        logger.info(f'Imported in {elapsed_time:.1f} seconds.', extra={'color': 'success'})
