import time
try:
    from xml.etree import cElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree

from textwrap import dedent


class Importer(object):

    def __init__(self, db):
        self.db = db

    def process(self, filepath):
        try:
            self.db.insertmany(self.get_snippets(filepath))
        except Exception:
            raise
        else:
            self.db.save()

    def get_snippets(self, filepath):
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
