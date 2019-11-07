import time
from textwrap import dedent

from .._types import AnyPath
from ..database.snippets_db import SnippetsDatabase

try:
    from xml.etree import cElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree


def import_xml(db: SnippetsDatabase, file_path: AnyPath):
    start_time = time.time()
    yield f'Importing snippets from {file_path}...'
    with db.connection:
        db.insertmany(_parse_snippets(file_path))

    elapsed_time = time.time() - start_time
    yield f'Finished importing in {elapsed_time:.1f} seconds.'


def _parse_snippets(filepath):
    now = int(time.time())
    for event, el in etree.iterparse(filepath):
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
