import time
from textwrap import dedent
from typing import Callable, TextIO
from xml.etree import ElementTree

from clisnips.database.snippets_db import SnippetsDatabase


def import_xml(db: SnippetsDatabase, file: TextIO, log: Callable):
    start_time = time.time()
    log(('info', f'Importing snippets from {file.name}...'))

    db.insert_many(_parse_snippets(file))
    log(('info', 'Rebuilding & optimizing search index...'))
    db.rebuild_index()
    db.optimize_index()

    elapsed_time = time.time() - start_time
    log(('success', f'Success: imported in {elapsed_time:.1f} seconds.'))


def _parse_snippets(file):
    now = int(time.time())
    for event, el in ElementTree.iterparse(file):
        if el.tag != 'snippet':
            continue
        row = {
            'title': el.findtext('title').strip(),
            'tag': el.findtext('tag').strip(),
            'cmd': dedent(el.findtext('command')),
            'doc': dedent(el.findtext('doc').strip()),
            'created_at': el.attrib.get('created-at', now),
            'last_used_at': el.attrib.get('last-used-at', now),
            'usage_count': el.attrib.get('usage-count', 0)
        }
        yield row
