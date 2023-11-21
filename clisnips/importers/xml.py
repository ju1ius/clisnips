import logging
import time
from collections.abc import Iterable
from pathlib import Path
from textwrap import dedent
from typing import TextIO
from xml.etree import ElementTree

from clisnips.database import ImportableSnippet

from .base import Importer, SnippetAdapter

logger = logging.getLogger(__name__)


class XmlImporter(Importer):
    def import_path(self, path: Path) -> None:
        start_time = time.time()
        logger.info(f'Importing snippets from {path}')

        with open(path) as fp:
            if self._dry_run:
                for _ in _parse_snippets(fp):
                    ...
            else:
                self._db.insert_many(_parse_snippets(fp))
            logger.info('Rebuilding & optimizing search index')
            if not self._dry_run:
                self._db.rebuild_index()
                self._db.optimize_index()

        elapsed_time = time.time() - start_time
        logger.info(f'Imported in {elapsed_time:.1f} seconds.', extra={'color': 'success'})


def _parse_snippets(file: TextIO) -> Iterable[ImportableSnippet]:
    now = int(time.time())
    for _, el in ElementTree.iterparse(file):
        if el.tag != 'snippet':
            continue
        yield SnippetAdapter.validate_python(
            {
                'title': el.findtext('title').strip(),
                'tag': el.findtext('tag').strip(),
                'cmd': dedent(el.findtext('command')),
                'doc': dedent(el.findtext('doc').strip()),
                'created_at': el.attrib.get('created-at', now),
                'last_used_at': el.attrib.get('last-used-at', 0),
                'usage_count': el.attrib.get('usage-count', 0),
                'ranking': el.attrib.get('ranking', 0.0),
            }
        )
